"""
Session orchestration service.

Coordinates the entire council session flow:
1. Initial responses from all configured providers
2. Chair merging of responses
3. Iteration cycles (feedback and re-merge)
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session
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
        # Map model configs to dict for provider factory
        model_configs = {}
        if config.model_configs:
            for mc in config.model_configs:
                model_configs[mc.provider] = mc.model

        # Create provider factory with runtime model configs (preserves API keys from env)
        if model_configs:
            self.provider_factory = ProviderFactory(model_configs=model_configs)
        # Otherwise use the existing factory initialized with default settings

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

        # Serialize selected providers to JSON if provided
        import json
        selected_providers_json = None
        if config.selected_providers:
            selected_providers_json = json.dumps(config.selected_providers)

        # Create session record
        session = Session(
            prompt=config.prompt,
            chair_provider=config.chair,
            total_iterations=config.iterations,
            merge_template=config.template,
            preset=config.preset,
            autopilot=config.autopilot,
            selected_providers=selected_providers_json,
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

                async for update in self._create_merge(session, feedback_responses, iteration):
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

    async def _collect_initial_responses(
        self, session: Session
    ) -> AsyncGenerator[dict, None]:
        """Collect initial responses from all configured providers in parallel."""
        import json

        providers = self.provider_factory.get_all_providers()
        provider_names = self.provider_factory.get_provider_names()

        if not providers:
            return

        # Filter providers based on selected_providers if specified
        if session.selected_providers:
            selected = json.loads(session.selected_providers)
            filtered_providers = []
            filtered_names = []
            for provider, name in zip(providers, provider_names):
                if name in selected:
                    filtered_providers.append(provider)
                    filtered_names.append(name)
            providers = filtered_providers
            provider_names = filtered_names

        if not providers:
            yield {
                "type": "error",
                "message": "No providers selected or available for this session",
            }
            return

        temperature = self._get_temperature_for_session(session)

        # Create wrapper coroutines that return provider name and model with result
        async def get_response_with_name(provider, name, prompt, temp):
            try:
                result = await self._get_provider_response(provider, prompt, temp)
                model = getattr(provider, 'model', 'unknown')
                return name, model, result, None
            except Exception as e:
                return name, None, None, e

        # Create tasks for all providers
        tasks = [
            get_response_with_name(provider, name, session.prompt, temperature)
            for provider, name in zip(providers, provider_names)
        ]

        # Run all providers in parallel and yield results as they complete
        for coro in asyncio.as_completed(tasks):
            provider_name, model, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "message": f"Failed to get response: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

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
        """Collect feedback from council on the merged response."""
        import json

        providers = self.provider_factory.get_all_providers()
        provider_names = self.provider_factory.get_provider_names()

        if not providers:
            return

        # Filter providers based on selected_providers if specified
        if session.selected_providers:
            selected = json.loads(session.selected_providers)
            filtered_providers = []
            filtered_names = []
            for provider, name in zip(providers, provider_names):
                if name in selected:
                    filtered_providers.append(provider)
                    filtered_names.append(name)
            providers = filtered_providers
            provider_names = filtered_names

        if not providers:
            return

        # Create feedback prompt
        feedback_prompt = f"""Please review and critique the following merged response:

{merged_response['content']}

Original prompt was: {session.prompt}

Provide constructive feedback on:
1. What works well
2. What could be improved
3. Any missing perspectives or considerations
4. Specific suggestions for enhancement"""

        # Create wrapper coroutines that return provider name and model with result
        async def get_feedback_with_name(provider, name, prompt, temp):
            try:
                result = await self._get_provider_response(provider, prompt, temp)
                model = getattr(provider, 'model', 'unknown')
                return name, model, result, None
            except Exception as e:
                return name, None, None, e

        provider_names = self.provider_factory.get_provider_names()
        temperature = self._get_temperature_for_session(session)

        # Create tasks for all providers
        tasks = [
            get_feedback_with_name(provider, name, feedback_prompt, temperature)
            for provider, name in zip(providers, provider_names)
        ]

        # Run all providers in parallel
        for coro in asyncio.as_completed(tasks):
            provider_name, model, result, error = await coro

            if error:
                yield {
                    "type": "error",
                    "provider": provider_name,
                    "message": f"Failed to get feedback: {str(error)}",
                }
                continue

            try:
                content, input_tokens, output_tokens, cost = result

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
                await self.db.refresh(response)

                yield {
                    "type": "feedback",
                    "iteration": iteration,
                    "provider": provider_name,
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
                    "message": f"Failed to get feedback: {str(e)}",
                }

    async def _create_merge(
        self, session: Session, responses: list[dict], iteration: int
    ) -> AsyncGenerator[dict, None]:
        """Chair creates a merged response from all inputs."""
        chair_provider = self.provider_factory.get_provider(session.chair_provider)

        if not chair_provider:
            yield {
                "type": "error",
                "message": f"Chair provider '{session.chair_provider}' is not configured",
            }
            return

        # Get merge template
        template = MERGE_TEMPLATES.get(session.merge_template, MERGE_TEMPLATES["balanced"])

        # Build merge prompt
        responses_text = "\n\n".join([
            f"--- Response from {r['provider']} ---\n{r['content']}"
            for r in responses
        ])

        if iteration == 1:
            merge_prompt = f"""{template}

Original prompt: {session.prompt}

Responses to merge:
{responses_text}

Please create a comprehensive merged response that synthesizes all of the above responses."""
        else:
            # For iteration cycles, adjust the template
            merge_prompt = f"""{template}

As the chair, review the feedback from the council and create an improved merged response.

Original prompt: {session.prompt}

Council feedback:
{responses_text}

Please create an improved merged response incorporating the feedback above."""

        # Get chair's merged response
        temperature = self._get_temperature_for_session(session)

        try:
            content, input_tokens, output_tokens, cost = await self._get_provider_response(
                chair_provider, merge_prompt, temperature
            )

            # Save to database
            response = Response(
                session_id=session.id,
                provider=session.chair_provider,
                model=getattr(chair_provider, 'model', 'unknown'),
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
        self, provider, prompt: str, temperature: float
    ) -> tuple[str, int, int, float]:
        """
        Get a complete response from a provider.

        Returns: (content, input_tokens, output_tokens, cost)
        """
        # Add file context to prompt if available
        full_prompt = prompt
        if self.file_context:
            full_prompt = f"{self.file_context}\n\n{prompt}"

        content = ""

        # Determine if we should send image data
        image_to_send = None
        if self.image_data and hasattr(provider, 'supports_vision') and provider.supports_vision():
            image_to_send = self.image_data

        # Collect streamed response
        async for chunk in provider.stream_completion(
            prompt=full_prompt,
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
