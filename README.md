# 🕵️ Drama Detective

An interactive CLI investigation tool for analyzing interpersonal drama using a multi-agent AI system.

## Why This Project?

Built to learn and experiment with **multi-agent system architecture**. Each agent specializes in a specific task, collaborating to conduct structured interviews and generate comprehensive analysis reports.

## Multi-Agent Architecture

The system uses **6 specialized AI agents**:

1. **Goal Generator** - Creates investigation objectives from incident summary
2. **Question Generator** - Generates contextual interview questions with multiple-choice answers
3. **Fact Extractor** - Extracts concrete claims from responses
4. **Drift Detector** - Identifies when answers go off-topic
5. **Goal Tracker** - Updates investigation progress based on new facts
6. **Analysis Agent** - Synthesizes all data into a final verdict with drama rating (1-10)

Each agent maintains its own prompt engineering and response format, demonstrating agent specialization and coordination.

## Features

- 📋 Interactive multiple-choice interviews (with custom answer option)
- 🎯 Dynamic goal tracking with confidence scores
- ⏰ Timeline reconstruction from gathered facts
- 🔥 Drama rating system (1-10 scale)
- 💾 Session persistence and resume capability
- 🎨 Rich CLI formatting with colors and tables

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd drama_detective

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or just 'activate' with the alias

# Install dependencies
pip install -e .
```

## Usage

### CLI Usage

```bash
# Start a new investigation
drama investigate "mexico-trip-drama"

# List all investigations
drama list

# Resume a paused investigation
drama resume <session-id>

# Analyze a completed investigation
drama analyze <session-id>
```

### API Server

Run the Flask API server for use with the React Native frontend:

```bash
# After installation, run the API server
drama-api

# Or run directly with Python
python src/api_server.py
```

The API server will be available at `http://localhost:5000` with the following endpoints:
- `POST /api/investigate` - Start a new investigation
- `POST /api/answer` - Submit an answer to a question
- `GET /api/sessions` - List all investigation sessions
- `GET /api/analysis/<session_id>` - Get analysis for a completed investigation

### Development with React Native Frontend

To run both the backend and frontend during development:

1. **Terminal 1 - Backend:**
   ```bash
   drama-api
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd path/to/react-native-app
   npm start
   ```

Alternatively, use a process manager like `concurrently` to start both at once (see package.json in frontend).

## Example Session

```
🕵️ Drama Detective
Starting investigation: mexico-trip-drama

Describe what happened: John and Rob went to Mexico together, and Lamar got upset...

First question: Why did Lamar get upset about this?
  A) Because Rob is his good friend
  B) Because he wasn't invited
  C) Because John is his ex
  D) Other (provide custom answer)

Your answer: A

[Interview continues with dynamic questions based on gathered facts...]

📊 Final Analysis Report
⚖️ Primary Responsibility: Rob (60%)
🔥 Drama Rating: 6/10
```

## Tech Stack

- **Python 3.9+** - Core language
- **Anthropic Claude API** - LLM for all agents
- **Flask** - REST API server
- **Flask-CORS** - Cross-origin resource sharing
- **Pydantic** - Data validation and models
- **Rich** - Terminal formatting
- **Click** - CLI framework

## Project Structure

```
src/
├── agents/          # 6 specialized AI agents
├── api/             # Flask REST API
│   ├── app.py       # Flask application factory
│   ├── routes.py    # API endpoints
│   └── utils.py     # API utilities
├── models.py        # Pydantic data models
├── prompts.py       # Agent system prompts
├── api_client.py    # Anthropic API wrapper
├── interview.py     # Orchestrator coordinating agents
├── session.py       # Session persistence
├── api_server.py    # API server entry point
├── cli.py           # CLI interface
└── report_formatter.py  # Analysis report display
```

## Learning Outcomes

- Agent specialization and coordination patterns
- Structured prompt engineering for different agent roles
- Managing conversation state across multiple agents
- Type-safe data flow between agents (using assertions)
- Balancing agent autonomy vs. orchestration

## License

MIT

---

*Built as a learning project for exploring multi-agent AI systems.*