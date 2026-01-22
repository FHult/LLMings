# LLMings - Installation Package

LLMings is a Multi-AI council with consensus building capabilities.

## Quick Start

### Prerequisites

1. **Python 3.10+** - Required for the backend
2. **Ollama** (optional) - For local AI models. Install from https://ollama.ai

### Running LLMings

**On macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**On Windows:**
```cmd
start.bat
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Configuration

1. Copy `.env.example` to `.env` (done automatically on first run)
2. Edit `.env` to add your API keys:
   - `OPENAI_API_KEY` - For GPT models
   - `ANTHROPIC_API_KEY` - For Claude models
   - `GOOGLE_API_KEY` - For Gemini models

### Using Ollama (Local Models)

If you have Ollama installed, the startup script will automatically start it.

To install models:
```bash
ollama pull llama3.3
ollama pull qwen3
ollama pull gemma3
```

### Stopping the Application

Press `Ctrl+C` in the terminal to stop all services.

## Directory Structure

```
install/
├── app/              # Backend Python application
├── static/           # Frontend build (served as static files)
├── venv/             # Python virtual environment (created on first run)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment configuration template
├── start.sh          # Startup script for macOS/Linux
├── start.bat         # Startup script for Windows
└── README.md         # This file
```

## Troubleshooting

### Port already in use
If port 3000 or 8000 is already in use, stop the other application or edit the startup script to use different ports.

### Python not found
Ensure Python 3.10+ is installed and available in your PATH.

### Ollama connection issues
If using local models, ensure Ollama is running: `ollama serve`

## License

MIT License
