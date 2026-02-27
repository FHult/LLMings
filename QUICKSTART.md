# HiveCouncil Quick Start Guide

## Prerequisites

- **Python 3.10+** installed
- **Node.js 22+** (Active LTS) and npm installed
- At least one AI provider API key (OpenAI, Anthropic, Google, or Grok)

## Setup (First Time Only)

### 1. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# You need at least one provider configured
nano .env  # or use your preferred editor
```

**Example .env:**
```bash
# Add at least one of these:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROK_API_KEY=...

# Optionally specify models (otherwise uses defaults):
# OPENAI_MODEL=gpt-4o
# ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### 2. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Running HiveCouncil

### Option A: Start Both Servers with One Command (Recommended)

```bash
# From the root directory
npm install  # First time only, to install concurrently
npm start
```

This will automatically:
- Start the FastAPI backend on http://localhost:8000
- Start the Vite frontend on http://localhost:5173
- Open your browser to http://localhost:5173

### Option B: Start Servers Separately

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## What You'll See

1. **Backend Status** indicator in the header (should show "✓ Backend Connected")
2. **Welcome message** explaining HiveCouncil
3. **Prompt Input** form with configuration options
4. **Model Selection** (click "▶ Model Selection" to expand)
5. **Advanced Options** (click "▶ Advanced Options" to expand)

## Quick Test

1. **Enter a prompt** like: "What are the key benefits of renewable energy?"
2. **Select chair** (which AI will merge responses): Choose any configured provider
3. **Set iterations**: Start with 1 or 2 for testing
4. **Click "Model Selection"** to see and choose specific models
5. **Click "Start Council Session"**

You should see:
- Session created successfully
- Session details displayed
- Note that streaming responses will be implemented in Phase 4

## Troubleshooting

### Backend won't start
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Check that all dependencies installed: `pip install -r requirements.txt`
- Verify at least one API key is in `.env`

### Frontend shows "Backend Offline"
- Make sure backend is running on port 8000
- Check backend terminal for errors
- Try accessing http://localhost:8000 directly

### "No AI providers configured"
- Add at least one API key to `.env` file
- Restart the backend server after adding keys
- Check that the `.env` file is in the root directory

### Port already in use
- Backend: Change port with `uvicorn app.main:app --reload --port 8001`
- Frontend: Vite will prompt you to use a different port

## API Endpoints (for testing)

- http://localhost:8000 - Backend root (shows status)
- http://localhost:8000/health - Health check
- http://localhost:8000/api/providers - List configured providers
- http://localhost:8000/docs - Interactive API documentation (Swagger UI)

## Next Steps

Once you've verified everything works:
1. Try different models for each provider
2. Experiment with different merge templates
3. Test the autopilot mode
4. Phase 4 will add real-time streaming of AI responses

## Support

- Documentation: See `docs/` folder
- Issues: https://github.com/FHult/LLMings/issues
- Architecture: See `ARCHITECTURE.md`
- Model Selection: See `docs/MODEL_SELECTION.md`
