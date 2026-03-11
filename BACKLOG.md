# LLMings — Improvement Backlog

Items deferred from code reviews. Ordered roughly by urgency/value.

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
