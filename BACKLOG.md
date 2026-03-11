# LLMings — Improvement Backlog

Items deferred from code reviews. Ordered roughly by urgency/value.

---

## HIGH — Technical Debt (from March 2026 code review)

### 10. Batch DB commits in the orchestrator's parallel task loops
**File**: `backend/app/services/session_orchestrator.py` lines 360-361, 455
Each response is committed individually inside `asyncio.as_completed()` loops. If one
commit fails mid-loop, some responses are saved and others are not — partial state.
Collect all responses first, bulk-insert, then commit once with a rollback on failure.
This also removes the serialised DB round-trip bottleneck from otherwise parallel work.

### 11. `model_configs` last-writer-wins for same-provider members
**File**: `backend/app/services/session_orchestrator.py` line 54-55
If two council members share a provider (e.g. two Anthropic members with different
models), only the last member's model ends up in `model_configs` used to initialise
the `ProviderFactory`. The per-call `provider.model` lock-swap mitigates runtime
breakage, but the factory is initialised with a wrong default. Fix: key `model_configs`
on `member.id` instead of `member.provider`, or remove the dict entirely since the
per-call override covers all cases.

---

## MEDIUM — Code Correctness / Deprecated APIs

### 12. `getattr` on a declared Pydantic field
**File**: `backend/app/api/routes/session.py` line 82
`resume_state = getattr(session_data, 'resume_state', None)` — `resume_state` is a
declared field on `SessionCreate`; the `getattr` guard silently hides future renames.
Replace with `session_data.resume_state`.

### 13. `datetime.utcnow` deprecated since Python 3.12
**Files**: `backend/app/models/session.py:16-17`, `backend/app/models/response.py:16`
`datetime.utcnow` returns a naïve datetime and is deprecated in Python 3.12, scheduled
for removal in 3.14. Replace with `datetime.now(timezone.utc)` and add
`from datetime import timezone`.

### 14. Module-level imports deferred into method bodies
**File**: `backend/app/services/session_orchestrator.py` lines 46, 750, 892
`import json` and `from app.services.ai_providers.ollama_provider import OllamaProvider`
are re-evaluated on every call. The OllamaProvider import appears twice. Move all three
to module level.

### 15. Deprecated `selected_providers` column still written on every insert
**Files**: `backend/app/models/session.py:41`, `backend/app/services/session_orchestrator.py:95`
The column is marked `# [DEPRECATED]` in the model but is still populated in
`create_session`. Either drop it via an Alembic migration or stop writing to it now.

### 16. Inert try/except in `AnthropicProvider.count_tokens`
**File**: `backend/app/services/ai_providers/anthropic_provider.py:76-80`
```python
try:
    return len(text) // 4   # Cannot raise
except Exception:
    return len(text) // 4   # Identical body
```
The try block is infallible. Either use Anthropic's `client.beta.messages.count_tokens()`
API for accuracy, or drop the dead try/except and document the approximation explicitly.

---

## LOW — Maintainability / Smell

### 17. Four-way code duplication in `_collect_*` orchestrator methods
**File**: `backend/app/services/session_orchestrator.py` lines 297-665
`_collect_initial_responses`, `_collect_responses_from_members`, `_collect_feedback`,
and `_collect_feedback_from_members` share ~80% identical code: task dispatch,
`asyncio.as_completed`, DB write, yield. Extract a shared `_dispatch_and_yield` helper
to reduce the file by ~150 lines and make future changes (e.g. #10 above) a single fix.

### 18. Unsupported-file error message leaks the full extension list
**File**: `backend/app/api/routes/files.py:36`
The 415 error detail includes the entire 40+ item sorted extension set. Point callers
to `GET /api/files/supported-types` instead:
`detail="Unsupported file type. See /api/files/supported-types for the full list."`

### 19. `image_data` held in memory for the full session lifetime
**File**: `backend/app/services/session_orchestrator.py:34,80`
Base64-encoded image data (up to ~13 MB for the 10 MB limit) is stored in
`self.image_data` from `_init_state_from_config` through all iterations. It is never
cleared after being consumed by the first provider call. For long multi-iteration
sessions this is unnecessary memory pressure. Clear after the initial-response phase.

### 20. Dead `if self.council_members:` guard in schema validator
**File**: `backend/app/schemas/session.py:67`
`council_members` has `min_length=1`, so the guard is always True. Remove it to
eliminate dead code and clarify intent.

---

## LOW VALUE / FUTURE

### 6. Ollama tool calling for council members
Ollama Python SDK 0.4 supports passing Python functions as tools. Council members could
call a `web_search` tool, calculator, or code runner mid-response. Requires:
- Define a set of shared tools in `backend/app/services/tools/`
- Pass tools to `OllamaProvider.stream_completion()` via the SDK `tools=` param
- Handle `tool_calls` in the streaming response loop

### 7. Ollama built-in web search
Ollama v0.17 ships a web search API (free tier for individuals). Could be surfaced as
an optional toggle per council session — particularly useful for strategy/research prompts.

### 19. Structured consensus: full architecture feature
Building on the Ollama structured output work (already done for chair synthesis),
extend the concept to a richer session summary view:
- Add a dedicated "Consensus Summary" panel in `LiveSession.tsx` showing agreements,
  disagreements, and confidence score in a visual format (progress bar for confidence,
  checkmarks for agreements, warning triangles for disagreements)
- Make the summary exportable as JSON alongside the existing session export formats
