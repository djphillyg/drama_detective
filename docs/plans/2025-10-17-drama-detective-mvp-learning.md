# Drama Detective MVP Implementation Plan (Learning Version)

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Build a CLI-based "Drama Detective" that investigates friend group drama using adaptive AI interviews with a sequential agent pipeline - while learning production Python patterns.

**Architecture:** Sequential agent chain where user provides drama summary, and AI conducts adaptive interview through Goal Generator → Fact Extractor → Drift Detector → Goal Tracker → Question Generator pipeline, concluding with Analysis Agent that generates verdict report.

**Tech Stack:** Python 3.10+, anthropic (Claude API), click (CLI), rich (terminal formatting), pydantic (validation), python-dotenv (config)

**Learning Focus:** This plan provides structure and imports, but YOU implement the logic. Learn by doing, not copying.

---

## High-Level Architecture Overview

### The Big Picture

This system implements a **conversational interview loop** where an AI detective asks questions and you (the user) provide answers. The system learns from your answers and adapts its questions accordingly.

### Core Flow (Simplified)

```
1. USER runs: drama investigate "cake incident"
2. USER provides summary: "Sarah forgot to bring the cake"
3. SYSTEM generates goals: ["establish timeline", "identify people", etc.]
4. SYSTEM asks first question: "What time was the party?"
5. USER answers: "It started at 5pm"
6. SYSTEM processes answer through agent pipeline:
   - Extract facts: "party started at 5pm"
   - Check drift: did answer address the question? yes
   - Update goals: timeline confidence goes from 0% → 30%
   - Generate next question: "When did Sarah arrive?"
7. Repeat steps 5-6 until all goals reach 80% confidence
8. USER runs: drama analyze <session-id>
9. SYSTEM generates report with timeline, facts, and verdict
```

### Key Concepts

**Session State** - Everything about an investigation is stored in a JSON file:
- `session_id`: unique identifier
- `goals`: list of investigation objectives with confidence scores
- `facts`: extracted claims from your answers
- `messages`: full conversation history
- `current_question`: what the AI just asked

**Sequential Agent Pipeline** - Every answer flows through multiple specialists:
1. **Fact Extractor**: pulls out concrete claims ("party started at 5pm")
2. **Drift Detector**: checks if you're staying on topic (every 3rd turn)
3. **Goal Tracker**: updates confidence scores based on new facts
4. **Question Generator**: creates next question targeting lowest-confidence goal

**Agent Design Pattern** - Each agent:
- Has a specialized system prompt (defines its job)
- Takes specific input (question + answer, or goals + facts)
- Returns structured JSON output (facts array, drift analysis, etc.)
- Uses Claude API under the hood

**Why This Architecture?**
- **Sequential** = Easy to debug (each agent has one job)
- **Stateful** = Can pause/resume anytime
- **Adaptive** = Questions get smarter as it learns more
- **Transparent** = You can see all facts extracted and goals tracked

### Data Models (Pydantic)

Think of these as the "shapes" of your data:

```python
Goal = {description: str, confidence: 0-100, status: not_started|in_progress|complete}
Fact = {topic: str, claim: str, timestamp: str, confidence: certain|uncertain}
Message = {role: assistant|user, content: str, timestamp: str}
Session = {session_id, incident_name, summary, goals[], facts[], messages[]}
```

### File Structure You'll Build

```
src/
├── models.py              # Pydantic schemas (Goal, Fact, Session, etc.)
├── session.py             # Save/load JSON files
├── api_client.py          # Talk to Claude API with retry logic
├── prompts.py             # System prompts for each agent
├── agents/
│   ├── goal_generator.py      # Creates investigation goals from summary
│   ├── fact_extractor.py      # Pulls facts from answers
│   ├── drift_detector.py      # Detects off-topic answers
│   ├── goal_tracker.py        # Updates goal confidence scores
│   ├── question_generator.py  # Creates next question
│   └── analysis_agent.py      # Final report generation
├── interview.py           # Orchestrates agent pipeline
├── report_formatter.py    # Pretty-print reports with Rich
└── cli.py                 # Click commands (investigate, list, analyze, resume)
```

### Testing Strategy

Each task follows **Test-Driven Development (TDD)**:
1. Write a failing test (defines what you want to build)
2. Run test → see it fail (proves test is real)
3. Write minimal code to pass test
4. Run test → see it pass (proves code works)
5. Commit

This means you always know if something breaks!

---

## Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/__init__.py`

**Step 1: Create requirements.txt**

```
anthropic>=0.18.0
click>=8.1.7
rich>=13.7.0
pydantic>=2.5.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-mock>=3.12.0
```

**Step 2: Create setup.py**

```python
from setuptools import setup, find_packages

setup(
    name="drama-detective",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # TODO: Copy from requirements.txt (production deps only)
    ],
    entry_points={
        "console_scripts": [
            # TODO: Map "drama" command to cli.py:cli function
        ],
    },
    python_requires=">=3.10",
)
```

**Step 3: Create .env.example**

```
# TODO: Add placeholder for ANTHROPIC_API_KEY
```

**Step 4: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Drama Detective data
.src/
```

**Step 5: Create package init file**

Create empty file: `src/__init__.py`

**Step 6: Install in development mode**

Run: `pip install -e .`
Expected: Package installed successfully

**Step 7: Create .env file**

Run: `cp .env.example .env`
Then manually add your Anthropic API key to `.env`

**Step 8: Commit**

```bash
git init
git add .
git commit -m "chore: initial project setup with dependencies"
```

---

## Task 2: Data Models and Pydantic Schemas

**Files:**
- Create: `src/models.py`
- Create: `tests/test_models.py`

**Step 1: Write test for Goal model**

File: `tests/test_models.py`

```python
import pytest
from src.models import Goal, GoalStatus

def test_goal_creation():
    # TODO: Create a Goal with description, status, confidence
    # Assert all fields are set correctly
    pass

def test_goal_confidence_bounds():
    # TODO: Create a Goal with confidence=150
    # Assert it gets clamped to 100
    # (Hint: Use Pydantic validator)
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_goal_creation -v`
Expected: FAIL with import error

**Step 3: Implement Goal model**

File: `src/models.py`

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GoalStatus(str, Enum):
    # TODO: Define NOT_STARTED, IN_PROGRESS, COMPLETE
    pass


class Goal(BaseModel):
    # TODO: Add fields:
    #   - description: str
    #   - status: GoalStatus (default NOT_STARTED)
    #   - confidence: int (default 0, constrained 0-100)

    @field_validator('confidence')
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        # TODO: Clamp value between 0 and 100
        pass


class Fact(BaseModel):
    # TODO: Add fields:
    #   - topic: str
    #   - claim: str
    #   - source: str (default "user")
    #   - timestamp: Optional[str]
    #   - confidence: str (default "certain")
    pass


class Message(BaseModel):
    # TODO: Add fields:
    #   - role: str (assistant or user)
    #   - content: str
    #   - timestamp: str
    pass


class SessionStatus(str, Enum):
    # TODO: Define ACTIVE, PAUSED, COMPLETE
    pass


class Session(BaseModel):
    # TODO: Add fields:
    #   - session_id: str
    #   - incident_name: str
    #   - created_at: str
    #   - status: SessionStatus (default ACTIVE)
    #   - summary: str (default "")
    #   - goals: list[Goal] (default empty)
    #   - messages: list[Message] (default empty)
    #   - facts: list[Fact] (default empty)
    #   - current_question: str (default "")
    #   - turn_count: int (default 0)
    pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All tests PASS

**Step 5: Write additional model tests**

File: `tests/test_models.py` (append)

```python
from src.models import Fact, Message, Session, SessionStatus
from datetime import datetime

def test_fact_creation():
    # TODO: Create a Fact and verify default values
    pass

def test_session_creation():
    # TODO: Create a Session with minimal required fields
    # Verify defaults are set correctly
    pass
```

**Step 6: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add pydantic models for session state"
```

---

## Task 3: Session Manager

**Files:**
- Create: `src/session.py`
- Create: `tests/test_session.py`

**Step 1: Write test for session creation**

File: `tests/test_session.py`

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from src.session import SessionManager
from src.models import SessionStatus

@pytest.fixture
def temp_data_dir():
    # TODO: Create temp directory, yield it, clean up after test
    pass

def test_create_session(temp_data_dir):
    # TODO: Create SessionManager with temp dir
    # Create new session
    # Assert session has correct name, status, ID
    pass

def test_save_and_load_session(temp_data_dir):
    # TODO: Create session, modify it, save it
    # Load it back
    # Assert loaded data matches original
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_session.py -v`
Expected: FAIL with import error

**Step 3: Implement SessionManager**

File: `src/session.py`

```python
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.models import Session, SessionStatus


class SessionManager:
    def __init__(self, data_dir: Optional[Path] = None):
        # TODO: Set data_dir (default: ~/.src/sessions)
        # Create directory if it doesn't exist
        pass

    def create_session(self, incident_name: str) -> Session:
        # TODO: Create Session with:
        #   - Random UUID for session_id
        #   - Current timestamp for created_at
        #   - ACTIVE status
        pass

    def save_session(self, session: Session) -> None:
        # TODO: Save session to JSON file
        # Filename: {session_id}.json
        # Use session.model_dump() to serialize
        pass

    def load_session(self, session_id: str) -> Session:
        # TODO: Load session from JSON file
        # Raise FileNotFoundError if not found
        # Use Session(**data) to deserialize
        pass

    def list_sessions(self) -> list[Session]:
        # TODO: Find all *.json files in data_dir
        # Load each one (skip corrupted files)
        # Return sorted by created_at (newest first)
        pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_session.py -v`
Expected: All tests PASS

**Step 5: Add test for list_sessions**

File: `tests/test_session.py` (append)

```python
def test_list_sessions(temp_data_dir):
    # TODO: Create 2 sessions, save both
    # Call list_sessions
    # Assert returns 2 sessions
    pass
```

**Step 6: Run tests**

Run: `pytest tests/test_session.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/session.py tests/test_session.py
git commit -m "feat: add session manager with save/load/list"
```

---

## Task 4: API Client Utilities

**Files:**
- Create: `src/api_client.py`
- Create: `tests/test_api_client.py`

**Step 1: Write test for API client initialization**

File: `tests/test_api_client.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.api_client import ClaudeClient

def test_client_initialization():
    # TODO: Mock environment variable for API key
    # Create ClaudeClient
    # Assert model and temperature are set
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_client.py -v`
Expected: FAIL with import error

**Step 3: Implement ClaudeClient**

File: `src/api_client.py`

```python
import os
import time
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        # TODO: Initialize Anthropic client with API key from env
        # Store model, temperature, max_tokens
        pass

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        # TODO: Call Claude API with retry logic
        # - Try up to max_retries times
        # - Use exponential backoff (2^attempt seconds)
        # - Return response.content[0].text
        # - Raise exception if all retries fail
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_client.py -v`
Expected: Test PASS

**Step 5: Add test for retry logic**

File: `tests/test_api_client.py` (append)

```python
def test_retry_logic():
    # TODO: Mock client.messages.create to fail twice, succeed third time
    # Call client.call()
    # Assert it retries and eventually succeeds
    # Assert create was called 3 times
    pass
```

**Step 6: Run tests**

Run: `pytest tests/test_api_client.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/api_client.py tests/test_api_client.py
git commit -m "feat: add Claude API client with retry logic"
```

---

## Task 5: Prompts Module

**Files:**
- Create: `src/prompts.py`

**Step 1: Create prompts module**

File: `src/prompts.py`

```python
"""System prompts for all agents in Drama Detective."""

GOAL_GENERATOR_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (generate 5-7 investigation goals)
# - Defines output format (JSON array of goal descriptions)
# - Provides example output
# - Lists guidelines (be specific, focus on facts, keep concise)
"""

FACT_EXTRACTOR_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (extract concrete claims)
# - Defines output format (JSON array with topic, claim, timestamp, confidence)
# - Provides example output
# - Lists guidelines (only concrete claims, mark uncertain statements)
"""

DRIFT_DETECTOR_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (check if answer addressed question)
# - Defines output format (JSON with addressed_question, drift_reason, redirect_suggestion)
# - Provides example output
# - Lists guidelines (be lenient, flag total avoidance)
"""

GOAL_TRACKER_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (update goal confidence based on facts)
# - Defines output format (JSON array with goal, confidence, status, reasoning)
# - Provides example output
# - Lists guidelines (mark complete at 80%, provide reasoning)
"""

QUESTION_GENERATOR_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (generate next interview question)
# - Defines output format (JSON with question, target_goal, reasoning)
# - Provides example output
# - Lists guidelines (prioritize low confidence, conversational tone)
"""

ANALYSIS_SYSTEM = """
# TODO: Write system prompt that:
# - Explains agent's job (synthesize findings into report)
# - Defines output format (JSON with timeline, key_facts, gaps, verdict)
# - Provides example output with verdict including drama_rating (1-10)
# - Lists guidelines (fair but honest, balanced percentages)
"""


def build_goal_generator_prompt(summary: str) -> str:
    # TODO: Format user prompt with summary
    # Ask for 5-7 goals as JSON array
    pass


def build_fact_extractor_prompt(question: str, answer: str) -> str:
    # TODO: Format user prompt with question and answer
    # Ask for extracted facts as JSON array
    pass


def build_drift_detector_prompt(question: str, answer: str) -> str:
    # TODO: Format user prompt with question and answer
    # Ask for drift analysis as JSON object
    pass


def build_goal_tracker_prompt(goals: list, new_facts: list) -> str:
    # TODO: Format goals and facts into readable text
    # Ask for updated confidence scores as JSON array
    pass


def build_question_generator_prompt(
    goals: list,
    facts: list,
    recent_messages: list,
    drift_redirect: str = None
) -> str:
    # TODO: Format goals, facts, recent messages into prompt
    # Include drift redirect if present
    # Ask for next question as JSON object
    pass


def build_analysis_prompt(session_data: dict) -> str:
    # TODO: Format complete session data into prompt
    # Ask for comprehensive analysis report as JSON
    pass
```

**Step 2: Commit**

```bash
git add src/prompts.py
git commit -m "feat: add system prompts for all agents"
```

---

## Task 6: Agent Implementation - Goal Generator

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/goal_generator.py`
- Create: `tests/test_agents/test_goal_generator.py`

**Step 1: Write test for goal generator**

File: `tests/test_agents/test_goal_generator.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.goal_generator import GoalGeneratorAgent
from src.models import Goal

def test_generate_goals():
    # TODO: Create agent
    # Mock client.call to return JSON array of goal descriptions
    # Call generate_goals()
    # Assert returns list of Goal objects with correct descriptions
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_goal_generator.py -v`
Expected: FAIL with import error

**Step 3: Implement GoalGeneratorAgent**

File: `src/agents/__init__.py` (empty file)

File: `src/agents/goal_generator.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import GOAL_GENERATOR_SYSTEM, build_goal_generator_prompt
from src.models import Goal, GoalStatus


class GoalGeneratorAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client (or create new one if None)
        pass

    def generate_goals(self, summary: str) -> list[Goal]:
        # TODO: Build user prompt from summary
        # Call Claude API with system + user prompt
        # Parse JSON response (handle cases where response has extra text)
        # Convert goal descriptions to Goal objects
        # Return list of Goal objects
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_goal_generator.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add src/agents/ tests/test_agents/
git commit -m "feat: implement goal generator agent"
```

---

## Task 7: Agent Implementation - Fact Extractor

**Files:**
- Create: `src/agents/fact_extractor.py`
- Create: `tests/test_agents/test_fact_extractor.py`

**Step 1: Write test for fact extractor**

File: `tests/test_agents/test_fact_extractor.py`

```python
import pytest
from unittest.mock import patch
from src.agents.fact_extractor import FactExtractorAgent
from src.models import Fact

def test_extract_facts():
    # TODO: Create agent
    # Mock client.call to return JSON array of fact objects
    # Call extract_facts(question, answer)
    # Assert returns list of Fact objects with correct data
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_fact_extractor.py -v`
Expected: FAIL with import error

**Step 3: Implement FactExtractorAgent**

File: `src/agents/fact_extractor.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import FACT_EXTRACTOR_SYSTEM, build_fact_extractor_prompt
from src.models import Fact


class FactExtractorAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client (or create new one if None)
        pass

    def extract_facts(self, question: str, answer: str) -> list[Fact]:
        # TODO: Build user prompt from question + answer
        # Call Claude API
        # Parse JSON response (handle extra text)
        # Convert fact dicts to Fact objects
        # Return list of Fact objects
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_fact_extractor.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add src/agents/fact_extractor.py tests/test_agents/test_fact_extractor.py
git commit -m "feat: implement fact extractor agent"
```

---

## Task 8: Agent Implementation - Drift Detector

**Files:**
- Create: `src/agents/drift_detector.py`
- Create: `tests/test_agents/test_drift_detector.py`

**Step 1: Write test for drift detector**

File: `tests/test_agents/test_drift_detector.py`

```python
import pytest
from unittest.mock import patch
from src.agents.drift_detector import DriftDetectorAgent

def test_detect_no_drift():
    # TODO: Create agent
    # Mock response showing question was addressed
    # Call check_drift(question, on-topic answer)
    # Assert addressed_question is True
    pass

def test_detect_drift():
    # TODO: Create agent
    # Mock response showing drift detected
    # Call check_drift(question, off-topic answer)
    # Assert addressed_question is False
    # Assert redirect_suggestion is present
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_drift_detector.py -v`
Expected: FAIL with import error

**Step 3: Implement DriftDetectorAgent**

File: `src/agents/drift_detector.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client
        pass

    def check_drift(self, question: str, answer: str) -> dict:
        # TODO: Build user prompt
        # Call Claude API
        # Parse JSON response
        # Return drift analysis dict
        pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agents/test_drift_detector.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/drift_detector.py tests/test_agents/test_drift_detector.py
git commit -m "feat: implement drift detector agent"
```

---

## Task 9: Agent Implementation - Goal Tracker

**Files:**
- Create: `src/agents/goal_tracker.py`
- Create: `tests/test_agents/test_goal_tracker.py`

**Step 1: Write test for goal tracker**

File: `tests/test_agents/test_goal_tracker.py`

```python
import pytest
from unittest.mock import patch
from src.agents.goal_tracker import GoalTrackerAgent
from src.models import Goal, Fact, GoalStatus

def test_update_goals():
    # TODO: Create agent
    # Mock response with updated confidence scores
    # Create initial goals and new facts
    # Call update_goals(goals, facts)
    # Assert confidence scores updated
    # Assert status updated based on confidence
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_goal_tracker.py -v`
Expected: FAIL with import error

**Step 3: Implement GoalTrackerAgent**

File: `src/agents/goal_tracker.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import GOAL_TRACKER_SYSTEM, build_goal_tracker_prompt
from src.models import Goal, Fact, GoalStatus


class GoalTrackerAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client
        pass

    def update_goals(self, goals: list[Goal], new_facts: list[Fact]) -> list[Goal]:
        # TODO: Return unchanged goals if no new facts
        # Convert goals and facts to dicts for prompt
        # Build user prompt
        # Call Claude API
        # Parse JSON response
        # Create update map by goal description
        # Apply updates to each goal
        # Return updated goals
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_goal_tracker.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add src/agents/goal_tracker.py tests/test_agents/test_goal_tracker.py
git commit -m "feat: implement goal tracker agent"
```

---

## Task 10: Agent Implementation - Question Generator

**Files:**
- Create: `src/agents/question_generator.py`
- Create: `tests/test_agents/test_question_generator.py`

**Step 1: Write test for question generator**

File: `tests/test_agents/test_question_generator.py`

```python
import pytest
from unittest.mock import patch
from src.agents.question_generator import QuestionGeneratorAgent
from src.models import Goal, Fact, Message

def test_generate_question():
    # TODO: Create agent with low-confidence goals
    # Mock response with new question
    # Call generate_question(goals, facts, messages)
    # Assert returns question dict with target_goal
    pass

def test_generate_wrap_up_when_goals_complete():
    # TODO: Create agent with all high-confidence goals
    # Mock or check that wrap-up question is generated
    # Assert target_goal == "wrap_up"
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_question_generator.py -v`
Expected: FAIL with import error

**Step 3: Implement QuestionGeneratorAgent**

File: `src/agents/question_generator.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import QUESTION_GENERATOR_SYSTEM, build_question_generator_prompt
from src.models import Goal, Fact, Message


class QuestionGeneratorAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client
        pass

    def generate_question(
        self,
        goals: list[Goal],
        facts: list[Fact],
        messages: list[Message],
        drift_redirect: str = None
    ) -> dict:
        # TODO: Calculate average confidence across goals
        # If avg >= 80%, return wrap-up question dict
        # Convert models to dicts for prompt
        # Build user prompt (include drift_redirect if present)
        # Call Claude API
        # Parse JSON response
        # Return question data dict
        pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agents/test_question_generator.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/question_generator.py tests/test_agents/test_question_generator.py
git commit -m "feat: implement question generator agent"
```

---

## Task 11: Agent Implementation - Analysis Agent

**Files:**
- Create: `src/agents/analysis_agent.py`
- Create: `tests/test_agents/test_analysis_agent.py`

**Step 1: Write test for analysis agent**

File: `tests/test_agents/test_analysis_agent.py`

```python
import pytest
from unittest.mock import patch
from src.agents.analysis_agent import AnalysisAgent

def test_generate_analysis():
    # TODO: Create agent
    # Mock response with complete analysis (timeline, facts, verdict, drama_rating)
    # Create session_data dict
    # Call generate_analysis(session_data)
    # Assert analysis has all required sections
    # Assert verdict has drama_rating
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_analysis_agent.py -v`
Expected: FAIL with import error

**Step 3: Implement AnalysisAgent**

File: `src/agents/analysis_agent.py`

```python
import json
from src.api_client import ClaudeClient
from src.prompts import ANALYSIS_SYSTEM, build_analysis_prompt


class AnalysisAgent:
    def __init__(self, client: ClaudeClient = None):
        # TODO: Store client
        pass

    def generate_analysis(self, session_data: dict) -> dict:
        # TODO: Build user prompt from session data
        # Call Claude API
        # Parse JSON response
        # Return analysis dict
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_analysis_agent.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add src/agents/analysis_agent.py tests/test_agents/test_analysis_agent.py
git commit -m "feat: implement analysis agent"
```

---

## Task 12: Interview Orchestrator

**Files:**
- Create: `src/interview.py`
- Create: `tests/test_interview.py`

**Step 1: Write test for interview orchestrator initialization**

File: `tests/test_interview.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.interview import InterviewOrchestrator
from src.models import Session

def test_orchestrator_initialization():
    # TODO: Create Session
    # Create InterviewOrchestrator with session
    # Assert session is stored
    # Assert turn_count starts at 0
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_interview.py -v`
Expected: FAIL with import error

**Step 3: Implement InterviewOrchestrator**

File: `src/interview.py`

```python
from datetime import datetime
from src.models import Session, Message, SessionStatus
from src.agents.goal_generator import GoalGeneratorAgent
from src.agents.fact_extractor import FactExtractorAgent
from src.agents.drift_detector import DriftDetectorAgent
from src.agents.goal_tracker import GoalTrackerAgent
from src.agents.question_generator import QuestionGeneratorAgent


class InterviewOrchestrator:
    """Orchestrates the sequential agent pipeline for conducting interviews."""

    def __init__(self, session: Session):
        # TODO: Store session
        # Initialize turn_count to 0
        # Initialize all agent instances
        pass

    def initialize_investigation(self, summary: str) -> str:
        # TODO: Store summary in session
        # Use goal_generator to create goals
        # Use question_generator to create first question
        # Store question in session.current_question
        # Add assistant message to session.messages
        # Return first question
        pass

    def process_answer(self, answer: str) -> tuple[str, bool]:
        """
        Process user's answer through agent pipeline.
        Returns: (next_question, is_complete)
        """
        # TODO: Increment turn_count
        # Add user message to session.messages
        # Extract facts using fact_extractor
        # Add facts to session.facts
        # Check drift every 3 turns using drift_detector
        # Update goals using goal_tracker
        # Generate next question using question_generator
        # Check if target_goal == "wrap_up" (is_complete)
        # Store next question in session
        # Add assistant message to session.messages
        # Update session status to COMPLETE if done
        # Return (next_question, is_complete)
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_interview.py -v`
Expected: Test PASS

**Step 5: Add integration test**

File: `tests/test_interview.py` (append)

```python
def test_process_answer_pipeline():
    # TODO: Create session with current_question and goals
    # Create orchestrator
    # Mock all agent methods
    # Call process_answer()
    # Assert next question returned
    # Assert messages added to session
    pass
```

**Step 6: Run tests**

Run: `pytest tests/test_interview.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/interview.py tests/test_interview.py
git commit -m "feat: implement interview orchestrator with agent pipeline"
```

---

## Task 13: CLI Commands - Basic Structure

**Files:**
- Create: `src/cli.py`

**Step 1: Implement basic CLI structure**

File: `src/cli.py`

```python
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from drama_detective.session import SessionManager

console = Console()


@click.group()
def cli():
    """🔍 Drama Detective - AI-powered drama investigation tool"""
    pass


@cli.command()
@click.argument('incident_name')
def investigate(incident_name):
    """Start a new drama investigation."""
    console.print(Panel.fit(
        "🔍 DRAMA DETECTIVE v1.0 🔍\nTruth-seeking AI interviewer",
        border_style="bold blue"
    ))

    console.print(f"\n[bold]Starting investigation:[/bold] {incident_name}\n")

    # Implementation will be added in next task
    console.print("[yellow]Investigation command - coming soon![/yellow]")


@cli.command()
def list():
    """List all investigations."""
    # Implementation will be added in next task
    console.print("[yellow]List command - coming soon![/yellow]")


@cli.command()
@click.argument('session_id')
def analyze(session_id):
    """Generate analysis report for an investigation."""
    # Implementation will be added in next task
    console.print(f"[yellow]Analyze command for {session_id} - coming soon![/yellow]")


@cli.command()
@click.argument('session_id')
def resume(session_id):
    """Resume a paused investigation."""
    # Implementation will be added in next task
    console.print(f"[yellow]Resume command for {session_id} - coming soon![/yellow]")


if __name__ == '__main__':
    cli()
```

**Step 2: Test CLI structure**

Run: `drama --help`
Expected: Shows help with all commands

Run: `drama investigate "test"`
Expected: Shows "coming soon" message

**Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat: add basic CLI structure with rich formatting"
```

---

## Task 14: CLI Commands - Investigate Implementation

**Files:**
- Modify: `src/cli.py`

**Step 1: Implement investigate command**

File: `src/cli.py` - Replace the `investigate` function:

```python
@cli.command()
@click.argument('incident_name')
def investigate(incident_name):
    # TODO: Print welcome banner
    # Prompt user for summary using console.input()
    # Validate summary is not empty
    # Create SessionManager and new session
    # Create InterviewOrchestrator
    # Initialize investigation (get first question)
    # Print first question

    # TODO: Start interview loop:
    # - Get user answer via console.input()
    # - Handle quit/exit/stop commands (save as paused)
    # - Validate answer not empty
    # - Process answer through orchestrator
    # - Save session after each turn
    # - If complete, print completion message with analyze command
    # - Print next question and continue loop
    pass
```

**Step 2: Test investigate command**

Run: `drama investigate "test incident"`
Expected: Prompts for summary, generates questions, allows answers

**Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat: implement investigate command with interview loop"
```

---

## Task 15: CLI Commands - List Implementation

**Files:**
- Modify: `src/cli.py`

**Step 1: Implement list command**

File: `src/cli.py` - Replace the `list` function:

```python
@cli.command()
def list():
    # TODO: Create SessionManager
    # Get all sessions
    # If empty, print helpful message about starting investigation

    # TODO: Create Rich Table with columns:
    # - ID (session_id, dim)
    # - Incident (incident_name, cyan)
    # - Status (color-coded: green/yellow/blue)
    # - Progress (calculate avg confidence %)
    # - Created (formatted timestamp)

    # TODO: Add row for each session
    # Print table
    pass
```

**Step 2: Test list command**

Run: `drama list`
Expected: Shows table of all investigations

**Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat: implement list command with rich table"
```

---

## Task 16: CLI Commands - Analyze Implementation

**Files:**
- Modify: `src/cli.py`
- Create: `src/report_formatter.py`

**Step 1: Create report formatter**

File: `src/report_formatter.py`

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def format_report(analysis: dict, incident_name: str, console: Console):
    # TODO: Print header with Panel

    # TODO: Print timeline section:
    # - Header with emoji
    # - Separator line
    # - Each event with formatted time

    # TODO: Print key facts section:
    # - Header with emoji
    # - Separator line
    # - Bulleted list of facts

    # TODO: Print gaps section (if any):
    # - Header with emoji
    # - Bulleted list of unanswered questions

    # TODO: Print verdict section:
    # - Header with emoji
    # - Primary responsibility with percentage
    # - Reasoning
    # - Contributing factors

    # TODO: Print drama rating:
    # - Rating as X/10
    # - Visual bar with fire emojis
    # - Explanation
    pass
```

**Step 2: Implement analyze command**

File: `src/cli.py` - Replace the `analyze` function:

```python
@cli.command()
@click.argument('session_id')
def analyze(session_id):
    # TODO: Create SessionManager
    # Load session (handle FileNotFoundError)
    # Print analyzing message
    # Create AnalysisAgent
    # Prepare session_data dict with model_dump()
    # Generate analysis
    # Format and display report using report_formatter
    pass
```

**Step 3: Test analyze command**

Run: `drama analyze <session_id>`
Expected: Shows formatted analysis report

**Step 4: Commit**

```bash
git add src/cli.py src/report_formatter.py
git commit -m "feat: implement analyze command with formatted report"
```

---

## Task 17: CLI Commands - Resume Implementation

**Files:**
- Modify: `src/cli.py`

**Step 1: Implement resume command**

File: `src/cli.py` - Replace the `resume` function:

```python
@cli.command()
@click.argument('session_id')
def resume(session_id):
    # TODO: Load session (handle FileNotFoundError)
    # Check if already complete (suggest analyze instead)
    # Print welcome banner
    # Print resuming message with stats
    # Show last question if present
    # Create InterviewOrchestrator
    # Set orchestrator.turn_count from session

    # TODO: Resume interview loop (similar to investigate):
    # - Get user answers
    # - Handle quit
    # - Process through orchestrator
    # - Save after each turn
    # - Handle completion
    pass
```

**Step 2: Test resume command**

Run: `drama resume <session_id>`
Expected: Resumes paused investigation from where it left off

**Step 3: Commit**

```bash
git add src/cli.py
git commit -m "feat: implement resume command for paused investigations"
```

---

## Task 18: Error Handling and Edge Cases

**Files:**
- Modify: `src/api_client.py`
- Modify: `src/interview.py`

**Step 1: Add better error handling to API client**

File: `src/api_client.py` - Update the `call` method:

```python
def call(
    self,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3
) -> str:
    # TODO: Wrap API call in retry loop
    # Handle specific error types:
    # - rate_limit: retry with exponential backoff
    # - invalid_api_key: raise clear error message
    # - context_length: raise clear error about conversation length
    # - Other errors: retry or raise with generic message
    pass
```

**Step 2: Add input validation to interview**

File: `src/interview.py` - Update `process_answer` method:

```python
def process_answer(self, answer: str) -> tuple[str, bool]:
    # TODO: Validate answer is not empty
    # Truncate very long answers (>2000 chars)
    # Then continue with existing implementation
    pass
```

**Step 3: Test error handling**

Create manual test scenarios:
- Empty API key → should show clear error
- Very long answer → should truncate
- Empty answer → should show validation error

**Step 4: Commit**

```bash
git add src/api_client.py src/interview.py
git commit -m "feat: add comprehensive error handling and input validation"
```

---

## Task 19: Documentation - README

**Files:**
- Create: `README.md`

**Step 1: Create comprehensive README**

File: `README.md`

```markdown
# 🔍 Drama Detective

<!-- TODO: Add sections:
- What is this? (brief description)
- Architecture diagram
- Quick Start (installation, first investigation)
- Example usage with sample output
- Technical details (tech stack, agents, state management)
- Development (how to run tests)
- Why I built this
- Future enhancements
- License
- Acknowledgments
-->
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with examples"
```

---

## Task 20: Final Polish and Testing

**Files:**
- Create: `examples/demo_transcript.md`
- Modify: `src/cli.py` (add version info)

**Step 1: Add version to CLI**

File: `src/cli.py` - Update the `cli` group:

```python
@click.group()
@click.version_option(version="1.0.0", prog_name="Drama Detective")
def cli():
    # TODO: Add enhanced docstring with usage hint
    pass
```

**Step 2: Create example transcript**

File: `examples/demo_transcript.md`

```markdown
# Demo Investigation Transcript

<!-- TODO: Document a complete investigation flow:
- Incident summary
- Full Q&A transcript
- Generated analysis report
- Shows what realistic usage looks like
-->
```

**Step 3: Run full integration test**

Test the complete flow:
1. Run `drama investigate "test"`
2. Complete an interview
3. Run `drama list`
4. Run `drama analyze <session-id>`
5. Verify all outputs look correct

**Step 4: Final commit**

```bash
git add examples/demo_transcript.md src/cli.py
git commit -m "feat: add version info and demo transcript"
```

---

## Success Criteria Checklist

At this point, you should have:

✅ Working CLI with all commands (investigate, list, analyze, resume)
✅ Multi-agent architecture with 6 specialized agents
✅ Sequential pipeline processing user responses
✅ Session state management with JSON persistence
✅ Comprehensive error handling
✅ Rich terminal formatting
✅ Analysis reports with timelines, facts, gaps, and verdicts
✅ Test coverage for all agents
✅ Complete documentation in README
✅ Example transcripts

---

## Learning Outcomes

By implementing this yourself (not copying), you learned:

1. **Production Python patterns:**
   - Pydantic for data validation
   - Dependency injection (passing clients to agents)
   - Test-driven development workflow
   - Proper error handling and retries

2. **Multi-agent AI systems:**
   - Sequential agent pipelines
   - Prompt engineering for specialized tasks
   - Structured output parsing
   - Conversational state management

3. **CLI development:**
   - Click for argument parsing
   - Rich for terminal formatting
   - Interactive user input
   - Command organization

4. **Software engineering practices:**
   - TDD: test first, code second
   - Small commits with clear messages
   - File organization and module structure
   - Separation of concerns

---

**Now go build it! You've got this.**