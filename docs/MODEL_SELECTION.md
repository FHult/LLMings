# Model Selection Guide

## Overview

HiveCouncil now supports selecting specific AI models for each provider. You can choose from multiple models for OpenAI (ChatGPT), Anthropic (Claude), Google (Gemini), and Grok (xAI).

## Configuration Methods

There are **three ways** to configure which models to use, in order of priority:

### 1. Runtime Configuration (Highest Priority)

Pass model configuration when creating a session via API:

```json
{
  "prompt": "Explain quantum computing",
  "chair": "anthropic",
  "iterations": 3,
  "model_configs": [
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "anthropic", "model": "claude-opus-4-20250514"},
    {"provider": "google", "model": "gemini-1.5-pro"}
  ]
}
```

This gives you **per-session control** over which models to use.

### 2. Environment Variables (Medium Priority)

Set model preferences in your `.env` file:

```bash
# OpenAI Model
OPENAI_MODEL=gpt-4o

# Anthropic Model
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Google Model
GOOGLE_MODEL=gemini-2.0-flash-exp

# Grok Model
GROK_MODEL=grok-beta
```

This sets a **global default** for all sessions.

### 3. Default Models (Fallback)

If no configuration is provided, HiveCouncil uses these defaults:

- **OpenAI**: `gpt-4o`
- **Anthropic**: `claude-sonnet-4-20250514`
- **Google**: `gemini-2.0-flash-exp`
- **Grok**: `grok-beta`

## Available Models

### OpenAI (ChatGPT)

| Model | Description | Pricing (per 1K tokens) |
|-------|-------------|-------------------------|
| `gpt-4o` | Latest GPT-4o, fast and capable | $2.50 / $10.00 |
| `gpt-4o-mini` | Smaller, faster, cheaper GPT-4o | $0.15 / $0.60 |
| `gpt-4-turbo` | GPT-4 Turbo with 128K context | $10.00 / $30.00 |
| `gpt-4` | Original GPT-4 | $30.00 / $60.00 |
| `gpt-3.5-turbo` | Fast and economical | $0.50 / $1.50 |

### Anthropic (Claude)

| Model | Description | Pricing (per 1K tokens) |
|-------|-------------|-------------------------|
| `claude-opus-4-20250514` | Most capable Claude model | $15.00 / $75.00 |
| `claude-sonnet-4-20250514` | Balanced performance and cost | $3.00 / $15.00 |
| `claude-sonnet-3-5-20241022` | Previous Sonnet version | $3.00 / $15.00 |
| `claude-sonnet-3-5-20240620` | Earlier Sonnet version | $3.00 / $15.00 |
| `claude-haiku-3-5-20241022` | Fast and lightweight | $0.80 / $4.00 |

### Google (Gemini)

| Model | Description | Pricing (per 1K tokens) |
|-------|-------------|-------------------------|
| `gemini-2.0-flash-exp` | Experimental 2.0 (FREE during preview) | $0.00 / $0.00 |
| `gemini-1.5-pro` | Most capable Gemini model | $1.25 / $5.00 |
| `gemini-1.5-flash` | Fast and efficient | $0.075 / $0.30 |
| `gemini-pro` | Original Gemini Pro | $0.50 / $1.50 |

### Grok (xAI)

| Model | Description | Pricing (per 1K tokens) |
|-------|-------------|-------------------------|
| `grok-beta` | Standard Grok model | $5.00 / $15.00 |
| `grok-vision-beta` | Grok with vision capabilities | $5.00 / $15.00 |

## API Endpoints

### Get All Providers and Models

```bash
GET /api/providers
```

**Response:**
```json
{
  "providers": {
    "openai": {
      "name": "openai",
      "current_model": "gpt-4o",
      "default_model": "gpt-4o",
      "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
      "configured": true
    },
    "anthropic": {
      "name": "anthropic",
      "current_model": "claude-sonnet-4-20250514",
      "default_model": "claude-sonnet-4-20250514",
      "available_models": [...],
      "configured": true
    }
    // ... other providers
  },
  "configured_count": 4
}
```

### Get Models for Specific Provider

```bash
GET /api/providers/openai/models
```

**Response:**
```json
{
  "provider": "openai",
  "default_model": "gpt-4o",
  "available_models": [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo"
  ]
}
```

## Use Cases

### Cost Optimization

Use cheaper models for less critical queries:

```json
{
  "model_configs": [
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "anthropic", "model": "claude-haiku-3-5-20241022"},
    {"provider": "google", "model": "gemini-1.5-flash"}
  ]
}
```

**Estimated cost**: ~$0.01-0.05 per query

### Maximum Quality

Use the most capable models for important decisions:

```json
{
  "model_configs": [
    {"provider": "openai", "model": "gpt-4"},
    {"provider": "anthropic", "model": "claude-opus-4-20250514"},
    {"provider": "google", "model": "gemini-1.5-pro"}
  ]
}
```

**Estimated cost**: ~$0.20-0.60 per query

### Balanced Approach (Default)

Use recommended models balancing cost and performance:

```json
{
  "model_configs": [
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    {"provider": "google", "model": "gemini-2.0-flash-exp"}
  ]
}
```

**Estimated cost**: ~$0.05-0.15 per query (Gemini 2.0 currently free)

### Testing New Models

Try experimental or newly released models:

```json
{
  "model_configs": [
    {"provider": "google", "model": "gemini-2.0-flash-exp"}
  ]
}
```

## Frontend Integration

When building the frontend UI, you can:

1. **Fetch available models** on app load:
   ```typescript
   const response = await fetch('/api/providers');
   const { providers } = await response.json();
   ```

2. **Display model selector** for each provider:
   ```typescript
   <Select>
     {providers.openai.available_models.map(model => (
       <option key={model} value={model}>{model}</option>
     ))}
   </Select>
   ```

3. **Submit with selected models**:
   ```typescript
   const modelConfigs = [
     { provider: 'openai', model: selectedOpenAIModel },
     { provider: 'anthropic', model: selectedAnthropicModel },
     // ...
   ];

   await createSession({
     prompt,
     chair,
     iterations,
     model_configs: modelConfigs
   });
   ```

## Cost Management Tips

1. **Set cheaper defaults** in `.env` for development:
   ```bash
   OPENAI_MODEL=gpt-4o-mini
   ANTHROPIC_MODEL=claude-haiku-3-5-20241022
   GOOGLE_MODEL=gemini-1.5-flash
   ```

2. **Override with premium models** when needed via runtime config

3. **Use Gemini 2.0 Flash** liberally (it's currently free!)

4. **Monitor costs** using the estimated_cost field in responses

## Model Selection Best Practices

### For the Council (Non-Chair)

- **Diverse perspectives**: Mix fast and capable models
- **Cost efficiency**: Use cheaper models for initial responses
- **Speed**: Prefer faster models for better UX

Example:
```json
{
  "model_configs": [
    {"provider": "openai", "model": "gpt-4o-mini"},        // Fast & cheap
    {"provider": "anthropic", "model": "claude-sonnet-4"}, // Balanced
    {"provider": "google", "model": "gemini-2.0-flash"}   // Free & fast
  ]
}
```

### For the Chair (Merger)

- **Quality matters**: Use a capable model
- **Context handling**: Needs to process all council responses
- **Synthesis ability**: Premium models work best

Recommended chairs:
- `claude-opus-4-20250514` - Best synthesis
- `claude-sonnet-4-20250514` - Good balance
- `gpt-4o` - Fast and capable

## Updating Models

As providers release new models:

1. **Add to PROVIDER_CONFIGS** in `backend/app/core/constants.py`:
   ```python
   "openai": {
       "available_models": [
           "gpt-4o",
           "new-model-name",  # Add here
           # ...
       ]
   }
   ```

2. **Add pricing** in PRICING dict:
   ```python
   "openai:new-model-name": (input_price, output_price),
   ```

3. **Update .env.example** with new model in comments

4. **Frontend will automatically** pick up new models via `/api/providers` endpoint

---

**Last Updated**: 2026-01-09
**Status**: ✅ Implemented
**GitHub**: https://github.com/FHult/HiveCouncil
