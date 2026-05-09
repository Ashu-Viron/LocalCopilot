# AI Workspace - Personal Coding Copilot

An AI-powered web-based coding assistant that can read, modify, and execute code in your local projects. Think of it as a self-hosted GitHub Copilot Workspace.

## Features

✨ **AI-Powered Chat** - Talk to an AI agent about your code
📁 **File Management** - Browse and edit files in your workspace
🖥️ **Code Editor** - Built-in Monaco editor with syntax highlighting
⚙️ **Tool Execution** - Run shell commands, git operations, and more
🔍 **Smart Search** - Search across your codebase
📊 **Diff Viewer** - Preview changes before applying them
🚀 **AWS Free Tier Ready** - Runs on a single t2.micro instance

## Architecture

```
Frontend (React + Vite) → Backend (FastAPI) → AI Agent (LiteLLM) → Local Workspace
```

### Tech Stack
- **Frontend**: React, Vite, Monaco Editor, TailwindCSS
- **Backend**: Python, FastAPI, Pydantic
- **AI**: LiteLLM (supports OpenAI, Gemini, Anthropic)
- **Deployment**: Docker, Nginx, AWS EC2

## Project Structure

```
LocalCopilot/
├── backend/           # Python FastAPI server
├── frontend/          # React + Vite application
├── static/            # Built frontend (served by backend)
├── workspace/         # User project files (sandboxed)
├── nginx/             # Nginx configuration
├── scripts/           # Deployment scripts
├── docker-compose.yml # Docker configuration
└── README.md
```

## Quick Start (Development)

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### ⚡ Quick Setup (Recommended)

```bash
# 1. Setup Python Virtual Environment
python setup_venv.py

# 2. Setup all dependencies
python dev_server.py setup

# 3. Start development servers
python dev_server.py start-all
```

Open http://localhost:5173 in your browser.

### 📚 Detailed Setup

#### Backend Setup
```bash
# Create and activate virtual environment
python setup_venv.py
source backend/venv/bin/activate  # Unix/macOS
# OR
backend\venv\Scripts\activate.bat  # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure API keys if needed

# Start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Virtual Environment Guide

For detailed virtual environment setup instructions, see:
- [VENV_SETUP.md](./VENV_SETUP.md) - Complete guide
- [VENV_QUICK_REFERENCE.md](./VENV_QUICK_REFERENCE.md) - Quick reference

### Integration & Testing

For testing and troubleshooting:
- [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - Full integration guide
- [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md) - Verification checklist
- [DEPENDENCY_TROUBLESHOOTING.md](./DEPENDENCY_TROUBLESHOOTING.md) - Dependency issues

## Deployment

### Docker
```bash
docker-compose up -d
```

### AWS EC2
See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step AWS deployment guide.

## Use Cases

### 1. Bug Fixing
Ask the AI to find and fix bugs in your code.

### 2. Feature Addition
Request new features and let the AI implement them.

### 3. Code Review
Get AI-powered code review and suggestions.

### 4. Learning
Understand how unfamiliar code works by asking questions.

## Security Notes

⚠️ **Workspace Restriction**: All file operations are restricted to the `/workspace` directory.
⚠️ **API Keys**: Keep your LLM API keys in `.env` and never expose them.
⚠️ **Command Execution**: Dangerous commands are blocked by default.

## Development Roadmap

- [x] Project structure
- [ ] Backend Core
- [ ] Frontend Components
- [ ] AI Agent Integration
- [ ] Docker & Deployment
- [ ] Advanced Features

## Contributing

Contributions are welcome! Please follow the existing code style and structure.

## License

MIT License - feel free to use this for projects, portfolios, or internships.

## Support

For issues or questions, open a GitHub issue or check the documentation.

---

**Built with ❤️ for developers who want their own AI assistant**
