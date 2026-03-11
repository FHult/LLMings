"""
Session orchestration service.

Coordinates the entire council session flow:
1. Initial responses from all configured providers
2. Chair merging of responses
3. Iteration cycles (feedback and re-merge)
"""

import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session
from app.models.response import Response
from app.schemas.session import SessionCreate
from app.schemas.consensus import ConsensusOutput
from app.services.ai_providers.provider_factory import ProviderFactory
from app.services.ai_providers.ollama_provider import OllamaProvider
from app.core.constants import MERGE_TEMPLATES, PRESET_CONFIGS
from app.core.personality_archetypes import get_archetype_system_prompt

logger = logging.getLogger(__name__)


class SessionOrchestrator:
    """Orchestrates multi-AI council sessions with iteration cycles."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_factory = ProviderFactory()
        self.file_context = ""  # Extracted text from files
        self.image_data = None  # Base64 image data for vision models
        # Per-provider asyncio locks prevent concurrent coroutines from mutating
        # provider.model on a shared instance at the same time.
        self._provider_locks: dict[str, asyncio.Lock] = {}

    def _get_temperature_for_session(self, session: Session) -> float:
        """Get temperature from session preset."""
        preset_config = PRESET_CONFIGS.get(session.preset, PRESET_CONFIGS["balanced"])
        return preset_config["temperature"]

    def _init_state_from_config(self, config: SessionCreate) -> None:
        """Initialise in-memory orchestrator state from a SessionCreate config.

        Separated from the DB write so the resume path can call this without
        creating an orphaned session row.
        """
        self.council_members = config.council_members

        # Initialise a fresh factory using settings/defaults.  Every call site
        # overrides the model per-request via the per-provider lock, so there is
        # no need to pass model_configs here (which would overwrite the factory
        # default when two members share the same provider with different models).
        self.provider_factory = ProviderFactory()

        self.member_personalities = {}
        self.member_thinking: dict[str, bool] = {}
        for member in config.council_members:
            personality_prompt = get_archetype_system_prompt(
                member.archetype,
                member.custom_personality
            )
            self.member_personalities[member.id] = personality_prompt
            self.member_thinking[member.id] = getattr(member, "enable_thinking", False)

        if config.files:
            file_texts = []
            for file in config.files:
                if file.extracted_text:
                    file_texts.append(f"=== File: {file.filename} ===\n{file.extracted_text}")
                if file.base64_data and not self.image_data:
                    self.image_data = file.base64_data
            if file_texts:
                self.file_context = "\n\n".join(file_texts)

    async def create_session(self, config: SessionCreate) -> Session:
        """Initialise orchestrator state and create a new session row in the DB."""
        self._init_state_from_config(config)

        chair_member = next((m for m in config.council_members if m.is_chair), config.council_members[0])
        council_members_json = json.dumps([m.dict() for m in config.council_members])

        session = Session(
            prompt=config.prompt,
            chair_provider=chair_member.provider,
            total_iterations=config.iterations,
            merge_template=config.template,
            preset=config.preset,
            autopilot=config.autopilot,
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

            # Image data has been consumed by initial responses; clear to free memory.
            self.image_data = None

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
            # Image data was consumed in the original session's initial responses.
            self.image_data = None

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

    async def _collect_from_members(
        self,
        session: Session,
        members: list,
        prompt: str,
        iteration: int,
        event_type: str,
    ) -> AsyncGenerator[dict, None]:
        """Dispatch requests to council members in parallel; stream events as results arrive.

        Pre-generates UUIDs so response IDs are available in SSE events before the DB
        write.  All inserts are committed in a single batch after the loop, reducing
        the N per-response commits to one.
        """
        if not members:
            return

        temperature = self._get_temperature_for_session(session)

        async def run_member(member, provider):
            try:
                result = await self._get_provider_response(
                    provider, prompt, temperature,
                    self.member_personalities.get(member.id),
                    model=member.model,
                    think=self.member_thinking.get(member.id, False),
                )
                return member.provider, member.id, member.role, member.model, result, None
            except Exception as e:
                return member.provider, member.id, member.role, None, None, e

        tasks = [
            run_member(member, self.provider_factory.get_provider(member.provider))
            for member in members
            if self.provider_factory.get_provider(member.provider)
        ]

        pending_responses = []
        for coro in asyncio.as_completed(tasks):
            provider_name, member_id, member_role, model, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "member_id": member_id,
                    "member_role": member_role,
                    "message": f"Failed to get response: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

                # Pre-generate the UUID so we can include it in the event now,
                # before the batch DB commit at the end of the loop.
                response_id = str(uuid.uuid4())
                response = Response(
                    id=response_id,
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
                pending_responses.append(response)

                yield {
                    "type": event_type,
                    "response_id": response_id,
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
                    "member_role": member_role,
                    "message": f"Failed to process response: {str(e)}",
                }

        if pending_responses:
            try:
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to commit {len(pending_responses)} responses to DB: {e}")

    async def _collect_initial_responses(
        self, session: Session
    ) -> AsyncGenerator[dict, None]:
        """Collect initial responses from all council members in parallel."""
        if not self.council_members:
            yield {"type": "error", "message": "No council members configured for this session"}
            return
        async for event in self._collect_from_members(
            session, self.council_members, session.prompt, 1, "initial_response"
        ):
            yield event

    async def _collect_responses_from_members(
        self, session: Session, members: list, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect initial responses from a specific subset of council members (resume path)."""
        async for event in self._collect_from_members(
            session, members, session.prompt, iteration, "initial_response"
        ):
            yield event

    async def _collect_feedback(
        self, session: Session, merged_response: dict, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect feedback from all council members on the merged response."""
        if not self.council_members:
            yield {"type": "error", "message": "No council members configured for this session"}
            return
        feedback_prompt = (
            f"Please review and critique the following merged response:\n\n"
            f"{merged_response['content']}\n\n"
            f"Original prompt was: {session.prompt}\n\n"
            f"Provide constructive feedback on:\n"
            f"1. What works well\n"
            f"2. What could be improved\n"
            f"3. Any missing perspectives or considerations\n"
            f"4. Specific suggestions for enhancement"
        )
        async for event in self._collect_from_members(
            session, self.council_members, feedback_prompt, iteration, "feedback"
        ):
            yield event

    async def _collect_feedback_from_members(
        self, session: Session, previous_output: dict, members: list, iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Collect feedback from a specific subset of council members (resume path)."""
        if not members or not previous_output:
            return
        prev_content = previous_output.get('content', '')
        feedback_prompt = (
            f"Original prompt: {session.prompt}\n\n"
            f"Previous output (iteration {iteration - 1}):\n{prev_content}\n\n"
            f"Please provide constructive feedback on this output. "
            f"What could be improved? What's working well? What's missing?"
        )
        async for event in self._collect_from_members(
            session, members, feedback_prompt, iteration, "feedback"
        ):
            yield event

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

        # Apply file context to merge prompt (mirrors _get_provider_response behaviour)
        full_merge_prompt = merge_prompt
        if self.file_context:
            full_merge_prompt = f"{self.file_context}\n\n{merge_prompt}"

        try:
            content: str
            structure_data: dict | None = None

            # When the chair is an Ollama model, use structured output so the
            # synthesis includes machine-readable agreements/disagreements metadata.
            chair_think = self.member_thinking.get(chair_member_id, False) if chair_member_id else False

            if isinstance(chair_provider, OllamaProvider):
                # Temporarily set model (same pattern as _get_provider_response)
                original_model = None
                if chair_model:
                    original_model = chair_provider.model
                    chair_provider.model = chair_model
                try:
                    json_str = await chair_provider.get_structured_completion(
                        prompt=full_merge_prompt,
                        system_prompt=chair_system_prompt,
                        temperature=temperature,
                        response_format=ConsensusOutput,
                        think=chair_think,
                    )
                    structured = ConsensusOutput.model_validate_json(json_str)
                    content = structured.synthesis
                    structure_data = structured.model_dump(exclude={"synthesis"})
                except Exception as struct_err:
                    logger.warning(
                        f"Structured output failed, falling back to streaming: {struct_err}"
                    )
                    content, *_ = await self._get_provider_response(
                        chair_provider, merge_prompt, temperature,
                        chair_system_prompt, model=chair_model, think=chair_think,
                    )
                finally:
                    if original_model is not None:
                        chair_provider.model = original_model
            else:
                content, *_ = await self._get_provider_response(
                    chair_provider, merge_prompt, temperature,
                    chair_system_prompt, model=chair_model,
                )

            input_tokens = chair_provider.count_tokens(full_merge_prompt)
            output_tokens = chair_provider.count_tokens(content)
            cost = chair_provider.estimate_cost(input_tokens, output_tokens)

            # Save to database
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

            event: dict = {
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
            if structure_data is not None:
                event["structure"] = structure_data

            yield event

        except Exception as e:
            yield {
                "type": "error",
                "message": f"Chair failed to create merge: {str(e)}",
            }

    def _get_provider_lock(self, provider_name: str) -> asyncio.Lock:
        """Return (creating if needed) a per-provider asyncio lock."""
        if provider_name not in self._provider_locks:
            self._provider_locks[provider_name] = asyncio.Lock()
        return self._provider_locks[provider_name]

    async def _get_provider_response(
        self, provider, prompt: str, temperature: float, system_prompt: str | None = None, model: str | None = None, think: bool = False
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

        provider_name = getattr(provider, 'name', '') or type(provider).__name__
        lock = self._get_provider_lock(provider_name)

        async with lock:
            # Set model on the shared provider instance under the lock so
            # concurrent coroutines cannot interleave their model assignments.
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
                stream_kwargs: dict = {
                    "prompt": full_prompt,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_tokens": 4000,
                    "image_data": image_to_send,
                }
                if think:
                    stream_kwargs["think"] = True
                async for chunk in provider.stream_completion(**stream_kwargs):
                    content += chunk

                # Use accurate token counts from Ollama's final chunk if available;
                # fall back to the rough character-based estimate for other providers.
                if isinstance(provider, OllamaProvider) and hasattr(provider, 'get_last_token_counts'):
                    input_tokens, output_tokens = provider.get_last_token_counts()
                    if not input_tokens:
                        input_tokens = provider.count_tokens(full_prompt)
                    if not output_tokens:
                        output_tokens = provider.count_tokens(content)
                else:
                    input_tokens = provider.count_tokens(full_prompt)
                    output_tokens = provider.count_tokens(content)
                cost = provider.estimate_cost(input_tokens, output_tokens)

                return content, input_tokens, output_tokens, cost
            finally:
                # Restore original model if we changed it
                if original_model is not None:
                    provider.model = original_model
