"""
Session orchestration service.

Coordinates the entire council session flow:
1. Initial responses from all configured providers
2. Chair merging of responses
3. Iteration cycles (feedback and re-merge)
"""

import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session

logger = logging.getLogger(__name__)

from app.models.response import Response
from app.schemas.session import SessionCreate
from app.services.ai_providers.provider_factory import ProviderFactory
from app.core.constants import MERGE_TEMPLATES, PRESET_CONFIGS


class SessionOrchestrator:
    """Orchestrates multi-AI council sessions with iteration cycles."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_factory = ProviderFactory()
        self.file_context = ""  # Extracted text from files
        self.image_data = None  # Base64 image data for vision models

    def _get_temperature_for_session(self, session: Session) -> float:
        """Get temperature from session preset."""
        preset_config = PRESET_CONFIGS.get(session.preset, PRESET_CONFIGS["balanced"])
        return preset_config["temperature"]

    async def create_session(self, config: SessionCreate) -> Session:
        """Create a new session in the database."""
        import json
        from app.core.personality_archetypes import get_archetype_system_prompt

        # Store council members configuration for use during execution
        self.council_members = config.council_members

        # Build model configs from council members
        model_configs = {}
        for member in config.council_members:
            model_configs[member.provider] = member.model

        # Create provider factory with runtime model configs
        if model_configs:
            self.provider_factory = ProviderFactory(model_configs=model_configs)

        # Store personality system prompts for each member
        self.member_personalities = {}
        for member in config.council_members:
            # Generate system prompt from archetype + custom personality
            personality_prompt = get_archetype_system_prompt(
                member.archetype,
                member.custom_personality
            )
            self.member_personalities[member.id] = personality_prompt

        # Process file attachments
        if config.files:
            file_texts = []
            for file in config.files:
                if file.extracted_text:
                    file_texts.append(f"=== File: {file.filename} ===\n{file.extracted_text}")
                # Store image data for vision models (use the first image)
                if file.base64_data and not self.image_data:
                    self.image_data = file.base64_data

            if file_texts:
                self.file_context = "\n\n".join(file_texts)

        # Get temperature from preset
        preset_config = PRESET_CONFIGS.get(config.preset, PRESET_CONFIGS["balanced"])
        temperature = preset_config["temperature"]

        # Find the chair member
        chair_member = next((m for m in config.council_members if m.is_chair), config.council_members[0])

        # Serialize council members and selected providers
        council_members_json = json.dumps([m.dict() for m in config.council_members])
        selected_providers_json = json.dumps([m.provider for m in config.council_members])

        # Create session record
        session = Session(
            prompt=config.prompt,
            chair_provider=chair_member.provider,
            total_iterations=config.iterations,
            merge_template=config.template,
            preset=config.preset,
            autopilot=config.autopilot,
            selected_providers=selected_providers_json,
            council_members=council_members_json,
            status="running",
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def run_session(self, session: Session) -> AsyncGenerator[dict, None]:
        """
        Run the complete session with iterations.

        Yields status updates as the session progresses:
        - {"type": "initial_response", "provider": "openai", "content": "...", "done": bool}
        - {"type": "merge", "iteration": 1, "content": "...", "done": bool}
        - {"type": "feedback", "iteration": 2, "provider": "openai", "content": "...", "done": bool}
        - {"type": "complete", "session_id": 123}
        """
        try:
            # Phase 1: Collect initial responses from all configured providers
            yield {"type": "status", "message": "Collecting initial responses from council..."}

            initial_responses = []
            async for update in self._collect_initial_responses(session):
                yield update
                if update.get("done"):
                    initial_responses.append(update)

            if not initial_responses:
                yield {"type": "error", "message": "No providers are configured with API keys"}
                session.status = "failed"
                await self.db.commit()
                return

            # Phase 2: Chair creates initial merge
            yield {"type": "status", "message": f"Chair ({session.chair_provider}) is merging responses..."}

            merged_response = None
            async for update in self._create_merge(session, initial_responses, iteration=1):
                yield update
                if update.get("done"):
                    merged_response = update

            # Phase 3: Iteration cycles (if total_iterations > 1)
            for iteration in range(2, session.total_iterations + 1):
                yield {"type": "status", "message": f"Starting iteration {iteration}/{session.total_iterations}..."}

                # Collect feedback from council on the merged response
                feedback_responses = []
                async for update in self._collect_feedback(session, merged_response, iteration):
                    yield update
                    if update.get("done"):
                        feedback_responses.append(update)

                # Chair merges feedback into improved response
                yield {"type": "status", "message": f"Chair is merging iteration {iteration} feedback..."}

                async for update in self._create_merge(session, feedback_responses, iteration, merged_response):
                    yield update
                    if update.get("done"):
                        merged_response = update

            # Complete
            session.status = "completed"
            await self.db.commit()

            yield {"type": "complete", "session_id": session.id}

        except Exception as e:
            session.status = "failed"
            await self.db.commit()
            yield {"type": "error", "message": str(e)}

    async def run_session_with_resume(self, session: Session, resume_state: dict) -> AsyncGenerator[dict, None]:
        """
        Resume a session from a paused state.

        Args:
            session: The session object
            resume_state: Dictionary containing:
                - current_iteration: Which iteration was in progress
                - responses: List of completed responses
                - merged_responses: List of completed merged responses
                - total_cost: Running cost
                - total_tokens: Running token counts

        Yields status updates as the session progresses.
        """
        try:
            current_iteration = resume_state.get('current_iteration', 1)
            existing_responses = resume_state.get('responses', [])
            existing_merged = resume_state.get('merged_responses', [])

            yield {"type": "status", "message": f"Resuming from iteration {current_iteration}..."}

            # Determine what phase we're in and what's missing
            # Count responses for current iteration
            current_iter_responses = [r for r in existing_responses if r.get('iteration') == current_iteration]
            current_iter_merged = [r for r in existing_merged if r.get('iteration') == current_iteration]

            # Get list of member IDs who have already responded in this iteration
            responded_member_ids = {r.get('member_id') for r in current_iter_responses if r.get('member_id')}

            # Get expected council members (excluding chair)
            non_chair_members = [m for m in self.council_members if not m.is_chair]
            expected_members = len(non_chair_members)

            # Find members who haven't responded yet
            missing_members = [m for m in non_chair_members if m.id not in responded_member_ids]

            merged_response = None
            if existing_merged:
                merged_response = existing_merged[-1]

            # Phase 1: Complete current iteration if needed
            if current_iteration == 1:
                # Initial responses phase
                if missing_members:
                    yield {"type": "status", "message": f"Requesting {len(missing_members)} missing initial response(s)..."}

                    initial_responses = list(current_iter_responses)
                    # Only collect from missing members
                    async for update in self._collect_responses_from_members(session, missing_members, iteration=1):
                        yield update
                        if update.get("done"):
                            initial_responses.append(update)
                else:
                    initial_responses = current_iter_responses

                # Create merge if not exists
                if not current_iter_merged:
                    yield {"type": "status", "message": f"Chair ({session.chair_provider}) is merging responses..."}
                    async for update in self._create_merge(session, initial_responses, iteration=1):
                        yield update
                        if update.get("done"):
                            merged_response = update

            else:
                # Feedback iteration phase
                if missing_members:
                    yield {"type": "status", "message": f"Requesting {len(missing_members)} missing feedback response(s) for iteration {current_iteration}..."}

                    feedback_responses = list(current_iter_responses)
                    # Only collect from missing members
                    async for update in self._collect_feedback_from_members(session, merged_response, missing_members, current_iteration):
                        yield update
                        if update.get("done"):
                            feedback_responses.append(update)
                else:
                    feedback_responses = current_iter_responses

                # Create merge if not exists
                if not current_iter_merged:
                    yield {"type": "status", "message": f"Chair is merging iteration {current_iteration} feedback..."}
                    async for update in self._create_merge(session, feedback_responses, current_iteration, merged_response):
                        yield update
                        if update.get("done"):
                            merged_response = update

            # Phase 2: Continue with remaining iterations
            for iteration in range(current_iteration + 1, session.total_iterations + 1):
                yield {"type": "status", "message": f"Starting iteration {iteration}/{session.total_iterations}..."}

                # Collect feedback from council on the merged response
                feedback_responses = []
                async for update in self._collect_feedback(session, merged_response, iteration):
                    yield update
                    if update.get("done"):
                        feedback_responses.append(update)

                # Chair merges feedback into improved response
                yield {"type": "status", "message": f"Chair is merging iteration {iteration} feedback..."}

                async for update in self._create_merge(session, feedback_responses, iteration, merged_response):
                    yield update
                    if update.get("done"):
                        merged_response = update

            # Complete
            session.status = "completed"
            await self.db.commit()

            yield {"type": "complete", "session_id": session.id}

        except Exception as e:
            session.status = "failed"
            await self.db.commit()
            yield {"type": "error", "message": str(e)}

    async def _collect_responses_from_members(
        self, session: Session, members: list, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect initial responses from specific council members."""
        if not members:
            return

        temperature = self._get_temperature_for_session(session)

        # Create wrapper coroutines
        async def get_response_with_name(provider, name, member_id, member_model, prompt, temp, system_prompt):
            try:
                result = await self._get_provider_response(provider, prompt, temp, system_prompt, model=member_model)
                return name, member_model, member_id, result, None
            except Exception as e:
                return name, None, member_id, None, e

        # Create tasks for specified members only
        tasks = []
        for member in members:
            provider = self.provider_factory.get_provider(member.provider)
            if provider:
                system_prompt = self.member_personalities.get(member.id)
                tasks.append(get_response_with_name(
                    provider, member.provider, member.id, member.model,
                    session.prompt, temperature, system_prompt
                ))

        # Run in parallel and yield results as they complete
        for coro in asyncio.as_completed(tasks):
            provider_name, model, member_id, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "message": f"Failed to get response: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

                # Get member role for display
                member_role = provider_name
                member = next((m for m in members if m.id == member_id), None)
                if member:
                    member_role = member.role

                # Save to database
                response = Response(
                    session_id=session.id,
                    provider=provider_name,
                    model=model,
                    iteration=iteration,
                    role="council",
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=cost,
                )
                self.db.add(response)
                await self.db.commit()

                yield {
                    "type": "initial_response",
                    "response_id": response.id,
                    "provider": provider_name,
                    "member_id": member_id,
                    "member_role": member_role,
                    "content": content,
                    "iteration": iteration,
                    "tokens": {"input": input_tokens, "output": output_tokens},
                    "cost": cost,
                    "done": True,
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "message": f"Failed to save response: {str(e)}",
                }

    async def _collect_feedback_from_members(
        self, session: Session, previous_output: dict, members: list, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect feedback from specific council members on previous output."""
        if not members or not previous_output:
            return

        temperature = self._get_temperature_for_session(session)
        prev_content = previous_output.get('content', '')

        feedback_prompt = f"""Original prompt: {session.prompt}

Previous output (iteration {iteration - 1}):
{prev_content}

Please provide constructive feedback on this output. What could be improved? What's working well? What's missing?"""

        # Create wrapper coroutines
        async def get_response_with_name(provider, name, member_id, member_model, prompt, temp, system_prompt):
            try:
                result = await self._get_provider_response(provider, prompt, temp, system_prompt, model=member_model)
                return name, member_model, member_id, result, None
            except Exception as e:
                return name, None, member_id, None, e

        # Create tasks for specified members only
        tasks = []
        for member in members:
            provider = self.provider_factory.get_provider(member.provider)
            if provider:
                system_prompt = self.member_personalities.get(member.id)
                tasks.append(get_response_with_name(
                    provider, member.provider, member.id, member.model,
                    feedback_prompt, temperature, system_prompt
                ))

        # Run in parallel and yield results as they complete
        for coro in asyncio.as_completed(tasks):
            provider_name, model, member_id, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "message": f"Failed to get feedback: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

                # Get member role for display
                member_role = provider_name
                member = next((m for m in members if m.id == member_id), None)
                if member:
                    member_role = member.role

                # Save to database
                response = Response(
                    session_id=session.id,
                    provider=provider_name,
                    model=model,
                    iteration=iteration,
                    role="council",
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=cost,
                )
                self.db.add(response)
                await self.db.commit()

                yield {
                    "type": "feedback",
                    "response_id": response.id,
                    "provider": provider_name,
                    "member_id": member_id,
                    "member_role": member_role,
                    "content": content,
                    "iteration": iteration,
                    "tokens": {"input": input_tokens, "output": output_tokens},
                    "cost": cost,
                    "done": True,
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "message": f"Failed to save feedback: {str(e)}",
                }

    async def _collect_initial_responses(
        self, session: Session
    ) -> AsyncGenerator[dict, None]:
        """Collect initial responses from all council members in parallel."""
        if not self.council_members:
            yield {
                "type": "error",
                "message": "No council members configured for this session",
            }
            return

        temperature = self._get_temperature_for_session(session)

        # Create wrapper coroutines that return provider name, model, and member info with result
        async def get_response_with_name(provider, name, member_id, member_model, prompt, temp, system_prompt):
            try:
                result = await self._get_provider_response(provider, prompt, temp, system_prompt, model=member_model)
                return name, member_model, member_id, result, None
            except Exception as e:
                return name, None, member_id, None, e

        # Create tasks for all council members
        tasks = []
        for member in self.council_members:
            provider = self.provider_factory.get_provider(member.provider)
            if provider:
                system_prompt = self.member_personalities.get(member.id)
                tasks.append(get_response_with_name(
                    provider, member.provider, member.id, member.model,
                    session.prompt, temperature, system_prompt
                ))

        # Run all council members in parallel and yield results as they complete
        for coro in asyncio.as_completed(tasks):
            provider_name, model, member_id, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "message": f"Failed to get response: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

                # Get member role for display
                member = next((m for m in self.council_members if m.id == member_id), None)
                member_role = member.role if member else provider_name

                # Save to database
                response = Response(
                    session_id=session.id,
                    provider=provider_name,
                    model=model,
                    iteration=1,
                    role="council",
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=cost,
                )
                self.db.add(response)
                await self.db.commit()
                await self.db.refresh(response)

                yield {
                    "type": "initial_response",
                    "provider": provider_name,
                    "member_role": member_role,
                    "member_id": member_id,
                    "content": content,
                    "tokens": {"input": input_tokens, "output": output_tokens},
                    "cost": cost,
                    "done": True,
                    "response_id": response.id,
                }

            except Exception as e:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "message": f"Failed to save response: {str(e)}",
                }

    async def _collect_feedback(
        self, session: Session, merged_response: dict, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect feedback from council members on the merged response."""
        if not self.council_members:
            yield {
                "type": "error",
                "message": "No council members configured for this session",
            }
            return

        # Create wrapper coroutines that return member info with result
        async def get_feedback_with_member(provider, member_id, member_role, member_model, prompt, temp, system_prompt):
            try:
                result = await self._get_provider_response(provider, prompt, temp, system_prompt, model=member_model)
                return member_id, member_role, member_model, result, None
            except Exception as e:
                return member_id, member_role, None, None, e

        temperature = self._get_temperature_for_session(session)

        # Create tasks for all council members
        tasks = []
        for member in self.council_members:
            provider = self.provider_factory.get_provider(member.provider)
            if provider:
                # Get member's personality system prompt
                system_prompt = self.member_personalities.get(member.id)

                # Create feedback prompt
                feedback_prompt = f"""Please review and critique the following merged response:

{merged_response['content']}

Original prompt was: {session.prompt}

Provide constructive feedback on:
1. What works well
2. What could be improved
3. Any missing perspectives or considerations
4. Specific suggestions for enhancement"""

                tasks.append(get_feedback_with_member(
                    provider, member.id, member.role, member.model,
                    feedback_prompt, temperature, system_prompt
                ))

        # Run all members in parallel
        for coro in asyncio.as_completed(tasks):
            member_id, member_role, model, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "member_id": member_id,
                    "member_role": member_role,
                    "message": f"Failed to get feedback: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

                # Save to database with member info
                response = Response(
                    session_id=session.id,
                    provider=member_id,  # Store member_id in provider field
                    model=model,
                    iteration=iteration,
                    role="council",
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=cost,
                )
                self.db.add(response)
                await self.db.commit()
                await self.db.refresh(response)

                yield {
                    "type": "feedback",
                    "iteration": iteration,
                    "provider": member_id,  # Use member_id as provider for consistency
                    "member_id": member_id,
                    "member_role": member_role,
                    "content": content,
                    "tokens": {"input": input_tokens, "output": output_tokens},
                    "cost": cost,
                    "done": True,
                    "response_id": response.id,
                }

            except Exception as e:
                yield {
                    "type": "error",
                    "member_id": member_id,
                    "member_role": member_role,
                    "message": f"Failed to get feedback: {str(e)}",
                }

    async def _create_merge(
        self, session: Session, responses: list[dict], iteration: int, previous_merge: dict = None
    ) -> AsyncGenerator[dict, None]:
        """Chair creates a merged response from all inputs."""
        chair_provider = self.provider_factory.get_provider(session.chair_provider)

        if not chair_provider:
            yield {
                "type": "error",
                "message": f"Chair provider '{session.chair_provider}' is not configured",
            }
            return

        # Get chair's personality system prompt, model, and role from council members
        chair_system_prompt = None
        chair_member_id = None
        chair_member_role = None
        chair_model = None
        if self.council_members:
            chair_member = next((m for m in self.council_members if m.is_chair), None)
            if chair_member:
                chair_system_prompt = self.member_personalities.get(chair_member.id)
                chair_member_id = chair_member.id
                chair_member_role = chair_member.role
                chair_model = chair_member.model

        # Build merge prompt
        responses_text = "\n\n".join([
            f"--- Response from {r['provider']} ---\n{r['content']}"
            for r in responses
        ])

        if iteration == 1:
            merge_prompt = f"""As the chair of this council, synthesize these council member responses into a single, concrete deliverable.

Original prompt: {session.prompt}

Council responses:
{responses_text}

Your task:
- If the original prompt contains content to be improved or revised (e.g., "improve this blog post: [content]"), create an IMPROVED VERSION of that specific content based on the council's feedback and suggestions. The council has reviewed the original content - now produce the enhanced version.
- If the prompt is an instruction or question without existing content, create the actual output requested (new content, answer, or analysis).

This should be a complete, ready-to-use result that incorporates the collective wisdom of the council - not just a summary of their opinions."""
        else:
            # For iteration cycles - use the previous merged output
            prev_content = previous_merge.get('content', 'No previous version available') if previous_merge else "No previous version available"

            merge_prompt = f"""As the chair, you must now produce the ACTUAL IMPROVED VERSION of the deliverable, incorporating the council's feedback.

Original prompt: {session.prompt}

Previous version (iteration {iteration - 1}):
{prev_content}

Council feedback:
{responses_text}

CRITICAL INSTRUCTIONS:
- DO NOT provide commentary, analysis, or suggestions
- DO NOT write "Title Revision Suggestion:" or similar meta-text
- DO NOT explain what changes you're making
- PRODUCE THE ACTUAL IMPROVED DELIVERABLE that directly fulfills the original prompt
- If it's an essay, write the full improved essay
- If it's code, write the full improved code
- If it's an analysis, write the full improved analysis

Begin your response with the actual deliverable content immediately."""

        # Get chair's merged response with their personality
        temperature = self._get_temperature_for_session(session)

        try:
            content, input_tokens, output_tokens, cost = await self._get_provider_response(
                chair_provider, merge_prompt, temperature, chair_system_prompt, model=chair_model
            )

            # Save to database (use chair_model if available, otherwise get from provider)
            model_to_save = chair_model if chair_model else getattr(chair_provider, 'model', 'unknown')
            response = Response(
                session_id=session.id,
                provider=session.chair_provider,
                model=model_to_save,
                iteration=iteration,
                role="chair",
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost,
            )
            self.db.add(response)
            await self.db.commit()
            await self.db.refresh(response)

            yield {
                "type": "merge",
                "iteration": iteration,
                "provider": session.chair_provider,
                "member_id": chair_member_id,
                "member_role": chair_member_role,
                "content": content,
                "tokens": {"input": input_tokens, "output": output_tokens},
                "cost": cost,
                "done": True,
                "response_id": response.id,
            }

        except Exception as e:
            yield {
                "type": "error",
                "message": f"Chair failed to create merge: {str(e)}",
            }

    async def _get_provider_response(
        self, provider, prompt: str, temperature: float, system_prompt: str | None = None, model: str | None = None
    ) -> tuple[str, int, int, float]:
        """
        Get a complete response from a provider.

        Args:
            provider: The AI provider instance
            prompt: The user prompt
            temperature: Temperature for generation
            system_prompt: Optional system prompt (personality/role instructions)
            model: Optional specific model to use (overrides provider's default)

        Returns: (content, input_tokens, output_tokens, cost)
        """
        # Add file context to prompt if available
        full_prompt = prompt
        if self.file_context:
            full_prompt = f"{self.file_context}\n\n{prompt}"

        content = ""

        # Temporarily set model if specified (for supporting multiple models per provider)
        original_model = None
        if model:
            original_model = provider.model
            provider.model = model

        try:
            # Determine if we should send image data
            image_to_send = None
            if self.image_data and hasattr(provider, 'supports_vision') and provider.supports_vision():
                image_to_send = self.image_data

            # Collect streamed response with personality system prompt
            async for chunk in provider.stream_completion(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=4000,
                image_data=image_to_send,
            ):
                content += chunk

            # Count tokens and estimate cost
            input_tokens = provider.count_tokens(full_prompt)
            output_tokens = provider.count_tokens(content)
            cost = provider.estimate_cost(input_tokens, output_tokens)

            return content, input_tokens, output_tokens, cost
        finally:
            # Restore original model if we changed it
            if original_model is not None:
                provider.model = original_model
