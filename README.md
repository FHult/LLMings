# LLMings (formerly HiveCouncil)

A local web application that creates a "council" of AI models to respond to user prompts, with iterative consensus-building through a designated Team Chair that synthesizes responses into a unified answer.

## Features

### Core Functionality
- **Multi-Provider Support**: Use OpenAI, Anthropic, Google Gemini, Grok, and Ollama (local models) simultaneously
- **Personality Archetypes**: Assign distinct personalities to council members (Analyst, Critic, Creative, Strategist, etc.)
- **Team Chair Synthesis**: Designated chair member synthesizes all responses into a coherent consensus
- **Iterative Refinement**: Run multiple iteration cycles where the council critiques and improves the consensus
- **Real-time Streaming**: Watch AI responses appear in real-time with smooth animations

### Council Configuration
- **Custom Council Members**: Configure each member with specific roles, personalities, and models
- **Template Save/Load**: Save and reuse council configurations for different use cases
- **Recommended Models**: Get model recommendations for each personality archetype
- **RAM Monitoring**: For Ollama models, see RAM requirements and compatibility

### Privacy & Storage
- **Local-First**: All data stored locally with SQLite, your prompts and responses stay private
- **Ollama Support**: Run powerful local models with complete privacy (no API calls)
- **File Attachments**: Attach files to provide context for council discussions
- **Export Sessions**: Export complete sessions to review later

## Tech Stack

- **Frontend**: React + Vite + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **AI Providers**: OpenAI, Anthropic, Google Gemini, Grok (xAI)

## Prerequisites

### Required
- **Node.js** 22+ (Active LTS) and npm
- **Python** 3.10+

### Optional (depending on which providers you want to use)
- **API Keys** for cloud providers:
  - [OpenAI API key](https://platform.openai.com/api-keys) - GPT-4, GPT-4o
  - [Anthropic API key](https://console.anthropic.com/) - Claude Opus, Sonnet, Haiku
  - [Google AI API key](https://makersuite.google.com/app/apikey) - Gemini models (free tier available)
  - [Grok API key](https://console.x.ai/) - Grok models

- **Ollama** for local models (completely free, no API keys needed):
  - [Install Ollama](https://ollama.ai/) - Run Llama, Mistral, Gemma, Phi, and more locally
  - System RAM: 8GB minimum, 16GB+ recommended for larger models

## Quick Start

### Option 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/FHult/LLMings.git
   cd LLMings
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Configure API keys (optional)**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys for cloud providers
   # Or skip this step to use only Ollama local models
   ```

4. **Start the application**
   ```bash
   npm start
   ```

   The app will start on [http://localhost:5173](http://localhost:5173)

### Option 2: Manual Setup

1. **Clone and setup backend**
   ```bash
   git clone https://github.com/FHult/LLMings.git
   cd LLMings/backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup frontend**
   ```bash
   cd ../frontend
   npm install
   ```

3. **Configure environment (optional)**
   ```bash
   cd ..
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start both services**
   ```bash
   # From the root directory
   npm start
   ```

### Getting Started with Ollama (Local Models)

If you want to use free local models without any API keys:

1. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Or download from https://ollama.ai
   ```

2. **Start Ollama**
   ```bash
   ollama serve
   ```

3. **Download models through the UI**
   - Go to Provider Settings tab in the app
   - Click "Manage Local Models" in the Ollama section
   - Install recommended models like llama3.1, mistral, or gemma2

No API keys needed - everything runs locally on your machine!

## Usage

### Basic Workflow

1. **Configure Providers** (first time only)
   - Click the "Provider Settings" tab
   - Add API keys for cloud providers you want to use
   - Or install Ollama models for free local inference

2. **Create Your Council**
   - Switch to "Council Session" tab
   - Click "+ Add Member" to add council members
   - For each member:
     - Set their role (e.g., "Technical Expert", "User Advocate")
     - Choose a personality archetype (affects their perspective)
     - Select provider and model
     - Optionally add custom personality instructions
   - Designate one member as Team Chair (they'll synthesize responses)

3. **Ask Your Question**
   - Type your question or prompt
   - Optionally attach files for context
   - Set number of iterations (1-10)
   - Click "Start Council Session"

4. **Watch the Council Work**
   - See each member respond with their unique perspective
   - Watch the chair synthesize responses into a unified answer
   - Iterate for refinement and deeper analysis

### Personality Archetypes

Choose from 14 distinct personalities for council members:
- **Balanced Analyst**: Well-rounded perspective
- **Optimist**: Positive, opportunity-focused
- **Critic**: Skeptical, identifies flaws
- **Pragmatist**: Practical, implementation-focused
- **Creative**: Innovative, outside-the-box thinking
- **Analyst**: Data-driven, logical reasoning
- **Devil's Advocate**: Challenges assumptions
- **Synthesizer**: Connects ideas, finds patterns (great for Chair)
- **Ethicist**: Moral and ethical considerations
- **Strategist**: Long-term planning and vision
- **Minimalist**: Simplicity and efficiency
- **Maximalist**: Comprehensive, ambitious approaches
- **Technical Expert**: Deep technical knowledge
- **User Advocate**: User experience focused
- **Researcher**: Evidence-based, thorough investigation

### Templates

Save and reuse council configurations:
- Click "💾 Save Team" after configuring your council
- Give it a descriptive name (e.g., "Technical Review Team", "Product Strategy Council")
- Load saved templates anytime with "📁 Load Team"

## Development

### Running in Development Mode

```bash
# Terminal 1: Backend with auto-reload
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend with hot module reload
cd frontend
npm run dev
```

### Database Migrations

The app uses SQLite and SQLAlchemy with automatic table creation. For manual migrations:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Project Structure

```
LLMings/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── lib/         # Utilities
│   │   ├── store/       # Zustand state management
│   │   └── types/       # TypeScript types
│   └── package.json
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── models/     # Database models
│   │   ├── services/   # Business logic
│   │   └── main.py     # FastAPI app
│   └── requirements.txt
├── docs/              # Documentation
├── REQUIREMENTS.md    # Requirements document
└── ARCHITECTURE.md    # Architecture plan
```

## Troubleshooting

### Backend won't start
- **Check Python version**: Requires Python 3.10+
  ```bash
  python3 --version
  ```
- **Virtual environment issues**: Delete `backend/venv` and recreate
  ```bash
  cd backend
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

### Frontend won't start
- **Check Node.js version**: Requires Node 22+ (Active LTS)
  ```bash
  node --version
  ```
- **Clear node_modules**:
  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

### Ollama models not showing
- **Ensure Ollama is running**:
  ```bash
  ollama serve
  ```
- **Check Ollama installation**:
  ```bash
  ollama list  # Should show installed models
  ```
- **Refresh providers**: Switch between tabs to refresh the model list

### API key errors
- Check `.env` file exists in project root
- Verify API keys are correctly formatted (no extra spaces)
- Test keys in Provider Settings tab - it will show if each provider is configured

### Models dropdown not updating after Ollama install
- Switch to "Council Session" tab to refresh (automatic provider reload)
- Or close and reopen the Ollama Manager modal

### Database errors
- Delete the database and let it recreate:
  ```bash
  rm hivecouncil.db
  npm start  # Database will be recreated automatically
  ```

## Documentation

- [Requirements Document](REQUIREMENTS.md) - Detailed requirements and features
- [Architecture Plan](ARCHITECTURE.md) - Technical architecture and design decisions

## Roadmap

- [ ] Export sessions to various formats (PDF, JSON, etc.)
- [ ] Session history and search
- [ ] Cost tracking and analytics
- [ ] Custom model parameters (temperature, max tokens, etc.)
- [ ] WebSocket support for real-time collaboration
- [ ] Docker deployment option

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) + [Vite](https://vitejs.dev/) - Fast frontend development
- [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [Zustand](https://zustand-demo.pmnd.rs/) - Lightweight state management
- [Ollama](https://ollama.ai/) - Run LLMs locally
