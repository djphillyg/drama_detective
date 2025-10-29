# Drama Detective MVP Implementation Plan

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Build a CLI-based "Drama Detective" that investigates friend group drama using adaptive AI interviews with a sequential agent pipeline.

**Architecture:** Sequential agent chain where user provides drama summary, and AI conducts adaptive interview through Goal Generator → Fact Extractor → Drift Detector → Goal Tracker → Question Generator pipeline, concluding with Analysis Agent that generates verdict report.

**Tech Stack:** Python 3.10+, anthropic (Claude API), click (CLI), rich (terminal formatting), pydantic (validation), python-dotenv (config)

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
drama_detective/
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

### Example Agent Logic (Fact Extractor)

**Input:**
- Question: "What time did the party start?"
- Answer: "It started at 5pm and Sarah was supposed to bring cake"

**System Prompt:**
```
You are a fact extraction agent.
Extract concrete claims from user responses.
Return JSON array of facts.
```

**User Prompt:**
```
Question asked: What time did the party start?
User's answer: It started at 5pm and Sarah was supposed to bring cake

Extract all concrete facts from this answer.
Return only the JSON array, no additional text.
```

**Claude Response:**
```json
[
  {"topic": "timing", "claim": "Party started at 5pm", "timestamp": "5pm", "confidence": "certain"},
  {"topic": "responsibility", "claim": "Sarah was supposed to bring cake", "confidence": "certain"}
]
```

**Agent Output:**
Returns list of `Fact` objects that get appended to `session.facts`

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
- Create: `drama_detective/__init__.py`

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
        "anthropic>=0.18.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "drama=drama_detective.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
```

**Step 3: Create .env.example**

```
ANTHROPIC_API_KEY=your_api_key_here
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
.drama_detective/
```

**Step 5: Create package init file**

Create empty file: `drama_detective/__init__.py`

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
- Create: `drama_detective/models.py`
- Create: `tests/test_models.py`

**Step 1: Write test for Goal model**

File: `tests/test_models.py`

```python
import pytest
from drama_detective.models import Goal, GoalStatus

def test_goal_creation():
    goal = Goal(
        description="Establish timeline of events",
        status=GoalStatus.NOT_STARTED,
        confidence=0
    )
    assert goal.description == "Establish timeline of events"
    assert goal.status == GoalStatus.NOT_STARTED
    assert goal.confidence == 0

def test_goal_confidence_bounds():
    goal = Goal(
        description="Test goal",
        status=GoalStatus.IN_PROGRESS,
        confidence=150
    )
    assert goal.confidence == 100  # Should cap at 100
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_goal_creation -v`
Expected: FAIL with import error

**Step 3: Implement Goal model**

File: `drama_detective/models.py`

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class Goal(BaseModel):
    description: str
    status: GoalStatus = GoalStatus.NOT_STARTED
    confidence: int = Field(default=0, ge=0, le=100)

    @field_validator('confidence')
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        return max(0, min(100, v))


class Fact(BaseModel):
    topic: str
    claim: str
    source: str = "user"
    timestamp: Optional[str] = None
    confidence: str = Field(default="certain")  # "certain" or "uncertain"


class Message(BaseModel):
    role: str  # "assistant" or "user"
    content: str
    timestamp: str


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETE = "complete"


class Session(BaseModel):
    session_id: str
    incident_name: str
    created_at: str
    status: SessionStatus = SessionStatus.ACTIVE
    summary: str = ""
    goals: list[Goal] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    current_question: str = ""
    turn_count: int = 0
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All tests PASS

**Step 5: Write additional model tests**

File: `tests/test_models.py` (append)

```python
from drama_detective.models import Fact, Message, Session, SessionStatus
from datetime import datetime

def test_fact_creation():
    fact = Fact(
        topic="cake incident",
        claim="Sarah forgot dessert",
        timestamp="5pm"
    )
    assert fact.topic == "cake incident"
    assert fact.confidence == "certain"

def test_session_creation():
    session = Session(
        session_id="test-123",
        incident_name="birthday drama",
        created_at=datetime.now().isoformat()
    )
    assert session.status == SessionStatus.ACTIVE
    assert len(session.goals) == 0
    assert session.turn_count == 0
```

**Step 6: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add drama_detective/models.py tests/test_models.py
git commit -m "feat: add pydantic models for session state"
```

---

## Task 3: Session Manager

**Files:**
- Create: `drama_detective/session.py`
- Create: `tests/test_session.py`

**Step 1: Write test for session creation**

File: `tests/test_session.py`

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from drama_detective.session import SessionManager
from drama_detective.models import SessionStatus

@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_session(temp_data_dir):
    manager = SessionManager(data_dir=temp_data_dir)
    session = manager.create_session("birthday cake disaster")

    assert session.incident_name == "birthday cake disaster"
    assert session.status == SessionStatus.ACTIVE
    assert len(session.session_id) > 0

def test_save_and_load_session(temp_data_dir):
    manager = SessionManager(data_dir=temp_data_dir)
    session = manager.create_session("test incident")
    session.summary = "A dramatic event occurred"

    manager.save_session(session)
    loaded = manager.load_session(session.session_id)

    assert loaded.session_id == session.session_id
    assert loaded.summary == "A dramatic event occurred"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_session.py -v`
Expected: FAIL with import error

**Step 3: Implement SessionManager**

File: `drama_detective/session.py`

```python
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from drama_detective.models import Session, SessionStatus


class SessionManager:
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path.home() / ".drama_detective" / "sessions"
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, incident_name: str) -> Session:
        """Create a new investigation session."""
        session = Session(
            session_id=str(uuid.uuid4()),
            incident_name=incident_name,
            created_at=datetime.now().isoformat(),
            status=SessionStatus.ACTIVE
        )
        return session

    def save_session(self, session: Session) -> None:
        """Save session to JSON file."""
        filepath = self.data_dir / f"{session.session_id}.json"
        with open(filepath, 'w') as f:
            json.dump(session.model_dump(), f, indent=2)

    def load_session(self, session_id: str) -> Session:
        """Load session from JSON file."""
        filepath = self.data_dir / f"{session_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(filepath, 'r') as f:
            data = json.load(f)
        return Session(**data)

    def list_sessions(self) -> list[Session]:
        """List all sessions."""
        sessions = []
        for filepath in self.data_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                sessions.append(Session(**data))
            except Exception:
                continue  # Skip corrupted files
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_session.py -v`
Expected: All tests PASS

**Step 5: Add test for list_sessions**

File: `tests/test_session.py` (append)

```python
def test_list_sessions(temp_data_dir):
    manager = SessionManager(data_dir=temp_data_dir)

    session1 = manager.create_session("incident 1")
    session2 = manager.create_session("incident 2")

    manager.save_session(session1)
    manager.save_session(session2)

    sessions = manager.list_sessions()
    assert len(sessions) == 2
    assert sessions[0].incident_name in ["incident 1", "incident 2"]
```

**Step 6: Run tests**

Run: `pytest tests/test_session.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add drama_detective/session.py tests/test_session.py
git commit -m "feat: add session manager with save/load/list"
```

---

## Task 4: API Client Utilities

**Files:**
- Create: `drama_detective/api_client.py`
- Create: `tests/test_api_client.py`

**Step 1: Write test for API client initialization**

File: `tests/test_api_client.py`

```python
import pytest
from unittest.mock import Mock, patch
from drama_detective.api_client import ClaudeClient

def test_client_initialization():
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        client = ClaudeClient()
        assert client.model == "claude-3-5-sonnet-20241022"
        assert client.temperature == 0.3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_client.py -v`
Expected: FAIL with import error

**Step 3: Implement ClaudeClient**

File: `drama_detective/api_client.py`

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
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        """Call Claude API with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)

        raise Exception("Failed to get response from Claude")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_client.py -v`
Expected: Test PASS

**Step 5: Add test for retry logic**

File: `tests/test_api_client.py` (append)

```python
from anthropic import APIError

def test_retry_logic():
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        client = ClaudeClient()

        # Mock the Anthropic client to fail twice then succeed
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]

        with patch.object(client.client.messages, 'create') as mock_create:
            mock_create.side_effect = [
                Exception("Rate limit"),
                Exception("Rate limit"),
                mock_response
            ]

            result = client.call("system", "user")
            assert result == "Success"
            assert mock_create.call_count == 3
```

**Step 6: Run tests**

Run: `pytest tests/test_api_client.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add drama_detective/api_client.py tests/test_api_client.py
git commit -m "feat: add Claude API client with retry logic"
```

---

## Task 5: Prompts Module

**Files:**
- Create: `drama_detective/prompts.py`

**Step 1: Create prompts module**

File: `drama_detective/prompts.py`

```python
"""System prompts for all agents in Drama Detective."""

GOAL_GENERATOR_SYSTEM = """You are a goal generation agent in the Drama Detective system.
Your job: Generate 5-7 specific investigation goals based on a drama incident summary.
Output format: Return a JSON array of goal descriptions.

Example output:
[
  "Establish chronological timeline of events",
  "Identify all people involved and their roles",
  "Understand the trigger or inciting incident",
  "Determine each person's perspective and motivations",
  "Clarify what was said or done by each party",
  "Assess current state of relationships between parties",
  "Identify emotional impact on those involved"
]

Guidelines:
- Be specific to the incident described
- Focus on factual questions (who, what, when, where, why)
- Keep goals concise (under 12 words each)
- Ensure goals are answerable through interview questions
"""

FACT_EXTRACTOR_SYSTEM = """You are a fact extraction agent in the Drama Detective system.
Your job: Extract concrete, verifiable claims from user responses.
Output format: Return a JSON array of facts.

Example output:
[
  {
    "topic": "timing",
    "claim": "The party started at 5pm",
    "timestamp": "5pm",
    "confidence": "certain"
  },
  {
    "topic": "attendance",
    "claim": "Sarah arrived 30 minutes late",
    "timestamp": "5:30pm",
    "confidence": "certain"
  }
]

Guidelines:
- Extract only concrete claims, not speculation or opinions
- Note any time references in the timestamp field
- Mark confidence as "certain" for definite statements, "uncertain" for "maybe" or "I think"
- Keep claims atomic (one fact per object)
- Ignore filler words and focus on substantive information
"""

DRIFT_DETECTOR_SYSTEM = """You are a drift detection agent in the Drama Detective system.
Your job: Determine if the user's answer actually addressed the question asked.
Output format: Return JSON object with drift analysis.

Example output:
{
  "addressed_question": false,
  "drift_reason": "User went on tangent about unrelated past incident",
  "redirect_suggestion": "Let's get back to the cake incident - what time did Sarah actually arrive?"
}

Guidelines:
- Check if answer contains relevant information to the question
- Flag rambling or excessive tangential information
- Suggest specific redirects that reference the original question
- Be lenient - partial answers are okay, total avoidance is not
"""

GOAL_TRACKER_SYSTEM = """You are a goal tracking agent in the Drama Detective system.
Your job: Update goal confidence scores based on newly extracted facts.
Output format: Return JSON array of goal updates.

Example output:
[
  {
    "goal": "Establish chronological timeline of events",
    "confidence": 75,
    "status": "in_progress",
    "reasoning": "We now have 3 time markers, but missing details about the middle period"
  },
  {
    "goal": "Identify all people involved and their roles",
    "confidence": 90,
    "status": "in_progress",
    "reasoning": "All major parties identified, just need clarification on Jordan's role"
  }
]

Guidelines:
- Increase confidence when new facts directly address a goal
- Mark status as "complete" when confidence >= 80
- Provide brief reasoning for confidence changes
- Consider both quantity and quality of information gathered
"""

QUESTION_GENERATOR_SYSTEM = """You are a question generation agent in the Drama Detective system.
Your job: Generate the next best interview question based on investigation state.
Output format: Return JSON object with question and metadata.

Example output:
{
  "question": "You mentioned Sarah arrived late - what time exactly did she get there, and did she explain why?",
  "target_goal": "Establish chronological timeline of events",
  "reasoning": "Timeline has gaps, this addresses the lowest confidence goal"
}

Guidelines:
- Prioritize goals with lowest confidence scores
- Reference previous answers to create natural conversation flow
- Ask one clear question at a time (not compound unless closely related)
- Use conversational tone, not interrogation style
- When drift was detected, incorporate the redirect suggestion
- If all goals above 80% confidence, ask wrap-up question to end interview
"""

ANALYSIS_SYSTEM = """You are an analysis agent in the Drama Detective system.
Your job: Synthesize all interview data into a comprehensive report.
Output format: Return JSON object with timeline, facts, gaps, and verdict.

Example output:
{
  "timeline": [
    {"time": "3:00pm", "event": "Sarah agreed to bring dessert"},
    {"time": "5:00pm", "event": "Party started, no cake arrived"}
  ],
  "key_facts": [
    "Sarah was responsible for bringing dessert",
    "No confirmation was sent in group chat",
    "Alex sent a reminder that wasn't acknowledged"
  ],
  "gaps": [
    "Did Sarah actually see the reminder message?",
    "Was there any prior discussion about backup plans?"
  ],
  "verdict": {
    "primary_responsibility": "Sarah",
    "percentage": 70,
    "reasoning": "Failed to confirm commitment and didn't communicate issues in advance",
    "contributing_factors": "Group didn't establish backup plan (30%)",
    "drama_rating": 6,
    "drama_rating_explanation": "Moderate - Solvable with honest conversation"
  }
}

Guidelines:
- Build timeline from facts with time references, chronologically ordered
- Summarize key facts without redundancy
- Identify genuine gaps where information is missing
- Provide balanced verdict with percentages adding to 100%
- Drama rating: 1-10 scale (1=minor misunderstanding, 10=friendship-ending)
- Be fair but don't avoid calling out problematic behavior
"""


def build_goal_generator_prompt(summary: str) -> str:
    return f"""Drama incident summary:
{summary}

Generate 5-7 specific investigation goals for this incident.
Return only the JSON array, no additional text."""


def build_fact_extractor_prompt(question: str, answer: str) -> str:
    return f"""Question asked: {question}

User's answer: {answer}

Extract all concrete facts from this answer.
Return only the JSON array, no additional text."""


def build_drift_detector_prompt(question: str, answer: str) -> str:
    return f"""Question asked: {question}

User's answer: {answer}

Did the user's answer address the question?
Return only the JSON object, no additional text."""


def build_goal_tracker_prompt(goals: list, new_facts: list) -> str:
    goals_text = "\n".join([f"- {g['description']} (current confidence: {g['confidence']}%)" for g in goals])
    facts_text = "\n".join([f"- {f['claim']}" for f in new_facts])

    return f"""Current investigation goals:
{goals_text}

Newly extracted facts:
{facts_text}

Update confidence scores for each goal based on these new facts.
Return only the JSON array, no additional text."""


def build_question_generator_prompt(
    goals: list,
    facts: list,
    recent_messages: list,
    drift_redirect: str = None
) -> str:
    goals_text = "\n".join([
        f"- {g['description']} (confidence: {g['confidence']}%, status: {g['status']})"
        for g in goals
    ])

    facts_text = "\n".join([f"- {f['claim']}" for f in facts[-10:]])  # Last 10 facts

    conversation_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in recent_messages[-6:]  # Last 3 exchanges
    ])

    drift_text = f"\n\nIMPORTANT: Previous answer went off-track. Suggested redirect: {drift_redirect}" if drift_redirect else ""

    return f"""Investigation goals:
{goals_text}

Facts gathered so far:
{facts_text}

Recent conversation:
{conversation_text}{drift_text}

Generate the next best question to ask.
Return only the JSON object, no additional text."""


def build_analysis_prompt(session_data: dict) -> str:
    goals_text = "\n".join([f"- {g['description']}" for g in session_data['goals']])
    facts_text = "\n".join([f"- {f['claim']}" for f in session_data['facts']])

    return f"""Complete interview data:

Incident: {session_data['incident_name']}
Summary: {session_data['summary']}

Investigation goals:
{goals_text}

All facts gathered:
{facts_text}

Generate comprehensive analysis report.
Return only the JSON object, no additional text."""
```

**Step 2: Commit**

```bash
git add drama_detective/prompts.py
git commit -m "feat: add system prompts for all agents"
```

---

## Task 6: Agent Implementation - Goal Generator

**Files:**
- Create: `drama_detective/agents/__init__.py`
- Create: `drama_detective/agents/goal_generator.py`
- Create: `tests/test_agents/test_goal_generator.py`

**Step 1: Write test for goal generator**

File: `tests/test_agents/test_goal_generator.py`

```python
import pytest
from unittest.mock import Mock, patch
from drama_detective.agents.goal_generator import GoalGeneratorAgent
from drama_detective.models import Goal

def test_generate_goals():
    agent = GoalGeneratorAgent()

    mock_response = """[
        "Establish timeline of events",
        "Identify all people involved",
        "Understand the trigger incident"
    ]"""

    with patch.object(agent.client, 'call', return_value=mock_response):
        goals = agent.generate_goals("Sarah forgot the cake at a birthday party")

        assert len(goals) == 3
        assert isinstance(goals[0], Goal)
        assert goals[0].description == "Establish timeline of events"
        assert goals[0].confidence == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_goal_generator.py -v`
Expected: FAIL with import error

**Step 3: Implement GoalGeneratorAgent**

File: `drama_detective/agents/__init__.py` (empty file)

File: `drama_detective/agents/goal_generator.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import GOAL_GENERATOR_SYSTEM, build_goal_generator_prompt
from drama_detective.models import Goal, GoalStatus


class GoalGeneratorAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def generate_goals(self, summary: str) -> list[Goal]:
        """Generate investigation goals from incident summary."""
        user_prompt = build_goal_generator_prompt(summary)
        response = self.client.call(GOAL_GENERATOR_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            goal_descriptions = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1
            goal_descriptions = json.loads(response[start:end])

        # Convert to Goal objects
        goals = [
            Goal(
                description=desc,
                status=GoalStatus.NOT_STARTED,
                confidence=0
            )
            for desc in goal_descriptions
        ]

        return goals
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_goal_generator.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/ tests/test_agents/
git commit -m "feat: implement goal generator agent"
```

---

## Task 7: Agent Implementation - Fact Extractor

**Files:**
- Create: `drama_detective/agents/fact_extractor.py`
- Create: `tests/test_agents/test_fact_extractor.py`

**Step 1: Write test for fact extractor**

File: `tests/test_agents/test_fact_extractor.py`

```python
import pytest
from unittest.mock import patch
from drama_detective.agents.fact_extractor import FactExtractorAgent
from drama_detective.models import Fact

def test_extract_facts():
    agent = FactExtractorAgent()

    mock_response = """[
        {
            "topic": "timing",
            "claim": "Party started at 5pm",
            "timestamp": "5pm",
            "confidence": "certain"
        }
    ]"""

    question = "What time did the party start?"
    answer = "The party started at 5pm and Sarah was supposed to be there with the cake."

    with patch.object(agent.client, 'call', return_value=mock_response):
        facts = agent.extract_facts(question, answer)

        assert len(facts) == 1
        assert isinstance(facts[0], Fact)
        assert facts[0].topic == "timing"
        assert facts[0].claim == "Party started at 5pm"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_fact_extractor.py -v`
Expected: FAIL with import error

**Step 3: Implement FactExtractorAgent**

File: `drama_detective/agents/fact_extractor.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import FACT_EXTRACTOR_SYSTEM, build_fact_extractor_prompt
from drama_detective.models import Fact


class FactExtractorAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def extract_facts(self, question: str, answer: str) -> list[Fact]:
        """Extract structured facts from user's answer."""
        user_prompt = build_fact_extractor_prompt(question, answer)
        response = self.client.call(FACT_EXTRACTOR_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            fact_dicts = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1
            fact_dicts = json.loads(response[start:end])

        # Convert to Fact objects
        facts = [Fact(**fact_dict) for fact_dict in fact_dicts]

        return facts
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_fact_extractor.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/fact_extractor.py tests/test_agents/test_fact_extractor.py
git commit -m "feat: implement fact extractor agent"
```

---

## Task 8: Agent Implementation - Drift Detector

**Files:**
- Create: `drama_detective/agents/drift_detector.py`
- Create: `tests/test_agents/test_drift_detector.py`

**Step 1: Write test for drift detector**

File: `tests/test_agents/test_drift_detector.py`

```python
import pytest
from unittest.mock import patch
from drama_detective.agents.drift_detector import DriftDetectorAgent

def test_detect_no_drift():
    agent = DriftDetectorAgent()

    mock_response = """{
        "addressed_question": true,
        "drift_reason": null,
        "redirect_suggestion": null
    }"""

    question = "What time did Sarah arrive?"
    answer = "She got there around 5:30pm."

    with patch.object(agent.client, 'call', return_value=mock_response):
        result = agent.check_drift(question, answer)

        assert result["addressed_question"] is True
        assert result["drift_reason"] is None

def test_detect_drift():
    agent = DriftDetectorAgent()

    mock_response = """{
        "addressed_question": false,
        "drift_reason": "User discussed unrelated past incident",
        "redirect_suggestion": "Let's focus on the cake incident - what time did Sarah arrive?"
    }"""

    question = "What time did Sarah arrive?"
    answer = "Well, last year she also forgot something important..."

    with patch.object(agent.client, 'call', return_value=mock_response):
        result = agent.check_drift(question, answer)

        assert result["addressed_question"] is False
        assert "unrelated past incident" in result["drift_reason"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_drift_detector.py -v`
Expected: FAIL with import error

**Step 3: Implement DriftDetectorAgent**

File: `drama_detective/agents/drift_detector.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def check_drift(self, question: str, answer: str) -> dict:
        """Check if user's answer addressed the question."""
        user_prompt = build_drift_detector_prompt(question, answer)
        response = self.client.call(DRIFT_DETECTOR_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            drift_analysis = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            drift_analysis = json.loads(response[start:end])

        return drift_analysis
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agents/test_drift_detector.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/drift_detector.py tests/test_agents/test_drift_detector.py
git commit -m "feat: implement drift detector agent"
```

---

## Task 9: Agent Implementation - Goal Tracker

**Files:**
- Create: `drama_detective/agents/goal_tracker.py`
- Create: `tests/test_agents/test_goal_tracker.py`

**Step 1: Write test for goal tracker**

File: `tests/test_agents/test_goal_tracker.py`

```python
import pytest
from unittest.mock import patch
from drama_detective.agents.goal_tracker import GoalTrackerAgent
from drama_detective.models import Goal, Fact, GoalStatus

def test_update_goals():
    agent = GoalTrackerAgent()

    mock_response = """[
        {
            "goal": "Establish timeline of events",
            "confidence": 65,
            "status": "in_progress",
            "reasoning": "Got 2 time markers but missing middle period"
        }
    ]"""

    goals = [Goal(description="Establish timeline of events", confidence=30)]
    new_facts = [Fact(topic="timing", claim="Party started at 5pm", timestamp="5pm")]

    with patch.object(agent.client, 'call', return_value=mock_response):
        updated_goals = agent.update_goals(goals, new_facts)

        assert len(updated_goals) == 1
        assert updated_goals[0].confidence == 65
        assert updated_goals[0].status == GoalStatus.IN_PROGRESS
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_goal_tracker.py -v`
Expected: FAIL with import error

**Step 3: Implement GoalTrackerAgent**

File: `drama_detective/agents/goal_tracker.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import GOAL_TRACKER_SYSTEM, build_goal_tracker_prompt
from drama_detective.models import Goal, Fact, GoalStatus


class GoalTrackerAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def update_goals(self, goals: list[Goal], new_facts: list[Fact]) -> list[Goal]:
        """Update goal confidence scores based on new facts."""
        if not new_facts:
            return goals

        # Convert to dicts for prompt
        goals_dict = [g.model_dump() for g in goals]
        facts_dict = [f.model_dump() for f in new_facts]

        user_prompt = build_goal_tracker_prompt(goals_dict, facts_dict)
        response = self.client.call(GOAL_TRACKER_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            updates = json.loads(response)
        except json.JSONDecodeError:
            start = response.find('[')
            end = response.rfind(']') + 1
            updates = json.loads(response[start:end])

        # Apply updates to goals
        update_map = {u["goal"]: u for u in updates}

        updated_goals = []
        for goal in goals:
            if goal.description in update_map:
                update = update_map[goal.description]
                goal.confidence = update["confidence"]
                goal.status = GoalStatus(update["status"])
            updated_goals.append(goal)

        return updated_goals
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_goal_tracker.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/goal_tracker.py tests/test_agents/test_goal_tracker.py
git commit -m "feat: implement goal tracker agent"
```

---

## Task 10: Agent Implementation - Question Generator

**Files:**
- Create: `drama_detective/agents/question_generator.py`
- Create: `tests/test_agents/test_question_generator.py`

**Step 1: Write test for question generator**

File: `tests/test_agents/test_question_generator.py`

```python
import pytest
from unittest.mock import patch
from drama_detective.agents.question_generator import QuestionGeneratorAgent
from drama_detective.models import Goal, Fact, Message

def test_generate_question():
    agent = QuestionGeneratorAgent()

    mock_response = """{
        "question": "What time did Sarah actually arrive?",
        "target_goal": "Establish timeline of events",
        "reasoning": "Timeline has gaps"
    }"""

    goals = [Goal(description="Establish timeline of events", confidence=40)]
    facts = [Fact(topic="timing", claim="Party started at 5pm")]
    messages = [
        Message(role="assistant", content="Tell me about the party", timestamp=""),
        Message(role="user", content="It was supposed to start at 5", timestamp="")
    ]

    with patch.object(agent.client, 'call', return_value=mock_response):
        result = agent.generate_question(goals, facts, messages)

        assert "What time" in result["question"]
        assert result["target_goal"] == "Establish timeline of events"

def test_generate_wrap_up_when_goals_complete():
    agent = QuestionGeneratorAgent()

    mock_response = """{
        "question": "Is there anything else you'd like to add about the incident?",
        "target_goal": "wrap_up",
        "reasoning": "All goals satisfied"
    }"""

    goals = [
        Goal(description="Goal 1", confidence=85, status="complete"),
        Goal(description="Goal 2", confidence=90, status="complete")
    ]
    facts = []
    messages = []

    with patch.object(agent.client, 'call', return_value=mock_response):
        result = agent.generate_question(goals, facts, messages)

        assert result["target_goal"] == "wrap_up"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_question_generator.py -v`
Expected: FAIL with import error

**Step 3: Implement QuestionGeneratorAgent**

File: `drama_detective/agents/question_generator.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import QUESTION_GENERATOR_SYSTEM, build_question_generator_prompt
from drama_detective.models import Goal, Fact, Message


class QuestionGeneratorAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def generate_question(
        self,
        goals: list[Goal],
        facts: list[Fact],
        messages: list[Message],
        drift_redirect: str = None
    ) -> dict:
        """Generate next interview question based on current state."""
        # Check if all goals are satisfied
        avg_confidence = sum(g.confidence for g in goals) / len(goals) if goals else 0

        if avg_confidence >= 80:
            return {
                "question": "Is there anything else you'd like to add about this incident that we haven't covered?",
                "target_goal": "wrap_up",
                "reasoning": "All investigation goals sufficiently addressed"
            }

        # Convert to dicts for prompt
        goals_dict = [g.model_dump() for g in goals]
        facts_dict = [f.model_dump() for f in facts]
        messages_dict = [m.model_dump() for m in messages]

        user_prompt = build_question_generator_prompt(
            goals_dict,
            facts_dict,
            messages_dict,
            drift_redirect
        )
        response = self.client.call(QUESTION_GENERATOR_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            question_data = json.loads(response)
        except json.JSONDecodeError:
            start = response.find('{')
            end = response.rfind('}') + 1
            question_data = json.loads(response[start:end])

        return question_data
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agents/test_question_generator.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/question_generator.py tests/test_agents/test_question_generator.py
git commit -m "feat: implement question generator agent"
```

---

## Task 11: Agent Implementation - Analysis Agent

**Files:**
- Create: `drama_detective/agents/analysis_agent.py`
- Create: `tests/test_agents/test_analysis_agent.py`

**Step 1: Write test for analysis agent**

File: `tests/test_agents/test_analysis_agent.py`

```python
import pytest
from unittest.mock import patch
from drama_detective.agents.analysis_agent import AnalysisAgent

def test_generate_analysis():
    agent = AnalysisAgent()

    mock_response = """{
        "timeline": [
            {"time": "5pm", "event": "Party started"}
        ],
        "key_facts": ["Sarah was responsible for dessert"],
        "gaps": ["Did Sarah see the reminder?"],
        "verdict": {
            "primary_responsibility": "Sarah",
            "percentage": 70,
            "reasoning": "Failed to confirm",
            "contributing_factors": "No backup plan (30%)",
            "drama_rating": 6,
            "drama_rating_explanation": "Moderate drama"
        }
    }"""

    session_data = {
        "incident_name": "cake disaster",
        "summary": "Sarah forgot the cake",
        "goals": [],
        "facts": []
    }

    with patch.object(agent.client, 'call', return_value=mock_response):
        analysis = agent.generate_analysis(session_data)

        assert "timeline" in analysis
        assert "verdict" in analysis
        assert analysis["verdict"]["drama_rating"] == 6
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents/test_analysis_agent.py -v`
Expected: FAIL with import error

**Step 3: Implement AnalysisAgent**

File: `drama_detective/agents/analysis_agent.py`

```python
import json
from drama_detective.api_client import ClaudeClient
from drama_detective.prompts import ANALYSIS_SYSTEM, build_analysis_prompt


class AnalysisAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client or ClaudeClient()

    def generate_analysis(self, session_data: dict) -> dict:
        """Generate comprehensive analysis report from interview data."""
        user_prompt = build_analysis_prompt(session_data)
        response = self.client.call(ANALYSIS_SYSTEM, user_prompt)

        # Parse JSON response
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError:
            start = response.find('{')
            end = response.rfind('}') + 1
            analysis = json.loads(response[start:end])

        return analysis
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents/test_analysis_agent.py -v`
Expected: Test PASS

**Step 5: Commit**

```bash
git add drama_detective/agents/analysis_agent.py tests/test_agents/test_analysis_agent.py
git commit -m "feat: implement analysis agent"
```

---

## Task 12: Interview Orchestrator

**Files:**
- Create: `drama_detective/interview.py`
- Create: `tests/test_interview.py`

**Step 1: Write test for interview orchestrator initialization**

File: `tests/test_interview.py`

```python
import pytest
from unittest.mock import Mock, patch
from drama_detective.interview import InterviewOrchestrator
from drama_detective.models import Session

def test_orchestrator_initialization():
    session = Session(
        session_id="test-123",
        incident_name="test incident",
        created_at="2024-01-01T00:00:00"
    )

    orchestrator = InterviewOrchestrator(session)
    assert orchestrator.session.session_id == "test-123"
    assert orchestrator.turn_count == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_interview.py -v`
Expected: FAIL with import error

**Step 3: Implement InterviewOrchestrator**

File: `drama_detective/interview.py`

```python
from datetime import datetime
from drama_detective.models import Session, Message, SessionStatus
from drama_detective.agents.goal_generator import GoalGeneratorAgent
from drama_detective.agents.fact_extractor import FactExtractorAgent
from drama_detective.agents.drift_detector import DriftDetectorAgent
from drama_detective.agents.goal_tracker import GoalTrackerAgent
from drama_detective.agents.question_generator import QuestionGeneratorAgent


class InterviewOrchestrator:
    """Orchestrates the sequential agent pipeline for conducting interviews."""

    def __init__(self, session: Session):
        self.session = session
        self.turn_count = 0

        # Initialize agents
        self.goal_generator = GoalGeneratorAgent()
        self.fact_extractor = FactExtractorAgent()
        self.drift_detector = DriftDetectorAgent()
        self.goal_tracker = GoalTrackerAgent()
        self.question_generator = QuestionGeneratorAgent()

    def initialize_investigation(self, summary: str) -> str:
        """Generate goals and first question from summary."""
        self.session.summary = summary

        # Generate investigation goals
        self.session.goals = self.goal_generator.generate_goals(summary)

        # Generate first question
        question_data = self.question_generator.generate_question(
            self.session.goals,
            self.session.facts,
            self.session.messages
        )

        first_question = question_data["question"]
        self.session.current_question = first_question

        # Add to message history
        self.session.messages.append(Message(
            role="assistant",
            content=first_question,
            timestamp=datetime.now().isoformat()
        ))

        return first_question

    def process_answer(self, answer: str) -> tuple[str, bool]:
        """
        Process user's answer through agent pipeline.
        Returns: (next_question, is_complete)
        """
        self.turn_count += 1

        # Add user answer to message history
        self.session.messages.append(Message(
            role="user",
            content=answer,
            timestamp=datetime.now().isoformat()
        ))

        # Step 1: Extract facts from answer
        new_facts = self.fact_extractor.extract_facts(
            self.session.current_question,
            answer
        )
        self.session.facts.extend(new_facts)

        # Step 2: Check for drift (every 3 turns)
        drift_redirect = None
        if self.turn_count % 3 == 0:
            drift_analysis = self.drift_detector.check_drift(
                self.session.current_question,
                answer
            )
            if not drift_analysis["addressed_question"]:
                drift_redirect = drift_analysis["redirect_suggestion"]

        # Step 3: Update goal confidence scores
        self.session.goals = self.goal_tracker.update_goals(
            self.session.goals,
            new_facts
        )

        # Step 4: Generate next question
        question_data = self.question_generator.generate_question(
            self.session.goals,
            self.session.facts,
            self.session.messages,
            drift_redirect
        )

        # Check if interview is complete
        is_complete = question_data["target_goal"] == "wrap_up"

        next_question = question_data["question"]
        self.session.current_question = next_question
        self.session.turn_count = self.turn_count

        # Add to message history
        self.session.messages.append(Message(
            role="assistant",
            content=next_question,
            timestamp=datetime.now().isoformat()
        ))

        if is_complete:
            self.session.status = SessionStatus.COMPLETE

        return next_question, is_complete
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_interview.py -v`
Expected: Test PASS

**Step 5: Add integration test**

File: `tests/test_interview.py` (append)

```python
def test_process_answer_pipeline():
    session = Session(
        session_id="test-123",
        incident_name="test incident",
        created_at="2024-01-01T00:00:00"
    )
    session.current_question = "What happened?"
    session.goals = [Mock(confidence=40)]

    orchestrator = InterviewOrchestrator(session)

    with patch.object(orchestrator.fact_extractor, 'extract_facts', return_value=[]):
        with patch.object(orchestrator.goal_tracker, 'update_goals', return_value=session.goals):
            with patch.object(orchestrator.question_generator, 'generate_question',
                            return_value={"question": "Next question?", "target_goal": "test"}):

                next_q, is_complete = orchestrator.process_answer("Something happened")

                assert next_q == "Next question?"
                assert is_complete is False
                assert len(session.messages) == 2  # User answer + assistant question
```

**Step 6: Run tests**

Run: `pytest tests/test_interview.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add drama_detective/interview.py tests/test_interview.py
git commit -m "feat: implement interview orchestrator with agent pipeline"
```

---

## Task 13: CLI Commands - Basic Structure

**Files:**
- Create: `drama_detective/cli.py`

**Step 1: Implement basic CLI structure**

File: `drama_detective/cli.py`

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
git add drama_detective/cli.py
git commit -m "feat: add basic CLI structure with rich formatting"
```

---

## Task 14: CLI Commands - Investigate Implementation

**Files:**
- Modify: `drama_detective/cli.py`

**Step 1: Implement investigate command**

File: `drama_detective/cli.py` - Replace the `investigate` function:

```python
@cli.command()
@click.argument('incident_name')
def investigate(incident_name):
    """Start a new drama investigation."""
    console.print(Panel.fit(
        "🔍 DRAMA DETECTIVE v1.0 🔍\nTruth-seeking AI interviewer",
        border_style="bold blue"
    ))

    console.print(f"\n[bold]Starting investigation:[/bold] {incident_name}\n")

    # Get incident summary
    console.print("[bold cyan]First, give me a brief summary of what happened:[/bold cyan]")
    summary = console.input("[dim]> [/dim]")

    if not summary.strip():
        console.print("[red]Error: Summary cannot be empty[/red]")
        return

    # Create session
    from drama_detective.session import SessionManager
    from drama_detective.interview import InterviewOrchestrator

    session_manager = SessionManager()
    session = session_manager.create_session(incident_name)

    # Initialize interview
    console.print("\n[yellow]⚙️  Analyzing situation and preparing questions...[/yellow]\n")
    orchestrator = InterviewOrchestrator(session)
    first_question = orchestrator.initialize_investigation(summary)

    console.print(f"[bold green]Detective:[/bold green] {first_question}\n")

    # Interview loop
    while True:
        user_answer = console.input("[dim]You: [/dim]")

        # Handle special commands
        if user_answer.lower() in ['quit', 'exit', 'stop']:
            session.status = "paused"
            session_manager.save_session(session)
            console.print(f"\n[yellow]Investigation paused. Resume with:[/yellow]")
            console.print(f"[cyan]drama resume {session.session_id}[/cyan]\n")
            break

        if not user_answer.strip():
            console.print("[dim]Please provide an answer, or type 'quit' to pause.[/dim]")
            continue

        # Process answer through pipeline
        console.print("\n[dim]⚙️  Analyzing response...[/dim]")
        next_question, is_complete = orchestrator.process_answer(user_answer)

        # Save state after each turn
        session_manager.save_session(session)

        if is_complete:
            console.print(f"\n[bold green]Detective:[/bold green] {next_question}\n")
            final_answer = console.input("[dim]You: [/dim]")

            if final_answer.strip():
                orchestrator.process_answer(final_answer)
                session_manager.save_session(session)

            console.print("\n[bold green]✓ Investigation complete![/bold green]")
            console.print(f"[cyan]Generate report with: drama analyze {session.session_id}[/cyan]\n")
            break

        console.print(f"\n[bold green]Detective:[/bold green] {next_question}\n")
```

**Step 2: Test investigate command**

Run: `drama investigate "test incident"`
Expected: Prompts for summary, generates questions, allows answers

**Step 3: Commit**

```bash
git add drama_detective/cli.py
git commit -m "feat: implement investigate command with interview loop"
```

---

## Task 15: CLI Commands - List Implementation

**Files:**
- Modify: `drama_detective/cli.py`

**Step 1: Implement list command**

File: `drama_detective/cli.py` - Replace the `list` function:

```python
@cli.command()
def list():
    """List all investigations."""
    from drama_detective.session import SessionManager

    session_manager = SessionManager()
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print("[yellow]No investigations found. Start one with:[/yellow]")
        console.print("[cyan]drama investigate \"incident name\"[/cyan]\n")
        return

    # Create table
    table = Table(title="Drama Investigations", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=36)
    table.add_column("Incident", style="cyan", width=30)
    table.add_column("Status", width=12)
    table.add_column("Progress", width=20)
    table.add_column("Created", style="dim", width=20)

    for session in sessions:
        # Calculate progress
        if session.goals:
            avg_confidence = sum(g.confidence for g in session.goals) / len(session.goals)
            progress = f"{avg_confidence:.0f}% complete"
        else:
            progress = "Not started"

        # Color code status
        status_color = {
            "active": "[green]Active[/green]",
            "paused": "[yellow]Paused[/yellow]",
            "complete": "[blue]Complete[/blue]"
        }
        status = status_color.get(session.status, session.status)

        # Format created date
        created = session.created_at[:19].replace('T', ' ')

        table.add_row(
            session.session_id,
            session.incident_name,
            status,
            progress,
            created
        )

    console.print(table)
    console.print()
```

**Step 2: Test list command**

Run: `drama list`
Expected: Shows table of all investigations

**Step 3: Commit**

```bash
git add drama_detective/cli.py
git commit -m "feat: implement list command with rich table"
```

---

## Task 16: CLI Commands - Analyze Implementation

**Files:**
- Modify: `drama_detective/cli.py`
- Create: `drama_detective/report_formatter.py`

**Step 1: Create report formatter**

File: `drama_detective/report_formatter.py`

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def format_report(analysis: dict, incident_name: str, console: Console):
    """Format analysis report with rich formatting."""

    # Header
    console.print("\n")
    console.print(Panel.fit(
        f"📊 ANALYSIS REPORT: {incident_name}",
        border_style="bold blue"
    ))

    # Timeline
    console.print("\n[bold cyan]📅 TIMELINE OF EVENTS[/bold cyan]")
    console.print("─" * 60)
    for event in analysis["timeline"]:
        console.print(f"[yellow]{event['time']:>10}[/yellow]  {event['event']}")

    # Key Facts
    console.print("\n[bold cyan]📋 KEY FACTS[/bold cyan]")
    console.print("─" * 60)
    for fact in analysis["key_facts"]:
        console.print(f"• {fact}")

    # Gaps
    if analysis["gaps"]:
        console.print("\n[bold cyan]❓ UNANSWERED QUESTIONS[/bold cyan]")
        console.print("─" * 60)
        for gap in analysis["gaps"]:
            console.print(f"• {gap}")

    # Verdict
    verdict = analysis["verdict"]
    console.print("\n[bold cyan]⚖️  VERDICT: Who's in the Wrong?[/bold cyan]")
    console.print("─" * 60)

    console.print(f"\n[bold]Primary responsibility:[/bold] {verdict['primary_responsibility']} ({verdict['percentage']}%)")
    console.print(f"  {verdict['reasoning']}")

    if verdict.get('contributing_factors'):
        console.print(f"\n[bold]Contributing factors:[/bold] {verdict['contributing_factors']}")

    # Drama rating
    rating = verdict['drama_rating']
    rating_bar = "🔥" * rating + "·" * (10 - rating)
    console.print(f"\n[bold]🎯 DRAMA RATING:[/bold] {rating}/10")
    console.print(f"   {rating_bar}")
    console.print(f"   {verdict['drama_rating_explanation']}")

    console.print("\n" + "═" * 60 + "\n")
```

**Step 2: Implement analyze command**

File: `drama_detective/cli.py` - Replace the `analyze` function:

```python
@cli.command()
@click.argument('session_id')
def analyze(session_id):
    """Generate analysis report for an investigation."""
    from drama_detective.session import SessionManager
    from drama_detective.agents.analysis_agent import AnalysisAgent
    from drama_detective.report_formatter import format_report

    session_manager = SessionManager()

    try:
        session = session_manager.load_session(session_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Session {session_id} not found[/red]")
        console.print("[yellow]Use 'drama list' to see all investigations[/yellow]\n")
        return

    console.print("\n[yellow]🔍 Analyzing investigation data...[/yellow]\n")

    # Generate analysis
    analysis_agent = AnalysisAgent()
    session_data = {
        "incident_name": session.incident_name,
        "summary": session.summary,
        "goals": [g.model_dump() for g in session.goals],
        "facts": [f.model_dump() for f in session.facts]
    }

    analysis = analysis_agent.generate_analysis(session_data)

    # Format and display report
    format_report(analysis, session.incident_name, console)
```

**Step 3: Test analyze command**

Run: `drama analyze <session_id>`
Expected: Shows formatted analysis report

**Step 4: Commit**

```bash
git add drama_detective/cli.py drama_detective/report_formatter.py
git commit -m "feat: implement analyze command with formatted report"
```

---

## Task 17: CLI Commands - Resume Implementation

**Files:**
- Modify: `drama_detective/cli.py`

**Step 1: Implement resume command**

File: `drama_detective/cli.py` - Replace the `resume` function:

```python
@cli.command()
@click.argument('session_id')
def resume(session_id):
    """Resume a paused investigation."""
    from drama_detective.session import SessionManager
    from drama_detective.interview import InterviewOrchestrator

    session_manager = SessionManager()

    try:
        session = session_manager.load_session(session_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Session {session_id} not found[/red]")
        console.print("[yellow]Use 'drama list' to see all investigations[/yellow]\n")
        return

    if session.status == "complete":
        console.print(f"[yellow]This investigation is already complete.[/yellow]")
        console.print(f"[cyan]View report with: drama analyze {session_id}[/cyan]\n")
        return

    console.print(Panel.fit(
        "🔍 DRAMA DETECTIVE v1.0 🔍\nTruth-seeking AI interviewer",
        border_style="bold blue"
    ))

    console.print(f"\n[bold]Resuming investigation:[/bold] {session.incident_name}\n")
    console.print(f"[dim]Turn {session.turn_count} | {len(session.facts)} facts gathered[/dim]\n")

    # Show last question
    if session.current_question:
        console.print(f"[bold green]Detective:[/bold green] {session.current_question}\n")

    # Resume interview
    orchestrator = InterviewOrchestrator(session)
    orchestrator.turn_count = session.turn_count

    while True:
        user_answer = console.input("[dim]You: [/dim]")

        if user_answer.lower() in ['quit', 'exit', 'stop']:
            session.status = "paused"
            session_manager.save_session(session)
            console.print(f"\n[yellow]Investigation paused again.[/yellow]\n")
            break

        if not user_answer.strip():
            console.print("[dim]Please provide an answer, or type 'quit' to pause.[/dim]")
            continue

        console.print("\n[dim]⚙️  Analyzing response...[/dim]")
        next_question, is_complete = orchestrator.process_answer(user_answer)
        session_manager.save_session(session)

        if is_complete:
            console.print(f"\n[bold green]Detective:[/bold green] {next_question}\n")
            final_answer = console.input("[dim]You: [/dim]")

            if final_answer.strip():
                orchestrator.process_answer(final_answer)
                session_manager.save_session(session)

            console.print("\n[bold green]✓ Investigation complete![/bold green]")
            console.print(f"[cyan]Generate report with: drama analyze {session.session_id}[/cyan]\n")
            break

        console.print(f"\n[bold green]Detective:[/bold green] {next_question}\n")
```

**Step 2: Test resume command**

Run: `drama resume <session_id>`
Expected: Resumes paused investigation from where it left off

**Step 3: Commit**

```bash
git add drama_detective/cli.py
git commit -m "feat: implement resume command for paused investigations"
```

---

## Task 18: Error Handling and Edge Cases

**Files:**
- Modify: `drama_detective/api_client.py`
- Modify: `drama_detective/interview.py`

**Step 1: Add better error handling to API client**

File: `drama_detective/api_client.py` - Update the `call` method:

```python
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        """Call Claude API with retry logic and better error handling."""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text

            except Exception as e:
                error_msg = str(e)

                # Handle specific error types
                if "rate_limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    raise Exception("Rate limit exceeded. Please try again in a moment.")

                elif "invalid_api_key" in error_msg.lower():
                    raise Exception("Invalid API key. Please check your .env file.")

                elif "context_length" in error_msg.lower():
                    raise Exception("Conversation too long. This is a known limitation.")

                # Generic retry for other errors
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API error: {error_msg}")

        raise Exception("Failed to get response from Claude after retries")
```

**Step 2: Add input validation to interview**

File: `drama_detective/interview.py` - Update `process_answer` method:

```python
    def process_answer(self, answer: str) -> tuple[str, bool]:
        """
        Process user's answer through agent pipeline.
        Returns: (next_question, is_complete)
        """
        # Validate input
        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty")

        # Truncate very long answers
        if len(answer) > 2000:
            answer = answer[:2000] + "..."

        self.turn_count += 1

        # ... rest of existing implementation
```

**Step 3: Test error handling**

Create manual test scenarios:
- Empty API key → should show clear error
- Very long answer → should truncate
- Empty answer → should show validation error

**Step 4: Commit**

```bash
git add drama_detective/api_client.py drama_detective/interview.py
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

An AI-powered CLI tool that investigates friend group drama through adaptive interviews. Built with a multi-agent architecture inspired by [Fractional AI's Superintelligent case study](https://www.fractional.ai/work/superintelligent).

## What is this?

Drama Detective conducts intelligent interviews to understand interpersonal conflicts. It uses a sequential agent pipeline where specialized AI agents work together to:

- Generate investigation goals from incident summaries
- Extract structured facts from conversational responses
- Detect when conversations drift off-topic
- Adaptively generate follow-up questions
- Synthesize findings into comprehensive reports with verdicts

While built as a portfolio project, it demonstrates real production AI patterns: conversational state management, multi-agent orchestration, and context-aware question generation.

## Architecture

```
User Answer
    ↓
[Fact Extractor] → Extract key claims
    ↓
[Drift Detector] → Check if answer on-topic
    ↓
[Goal Tracker] → Update investigation progress
    ↓
[Question Generator] → Create next question
    ↓
Display to User
```

Each agent is powered by Claude (Anthropic), with specialized system prompts and structured JSON outputs validated via Pydantic.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd drama_detective

# Install dependencies
pip install -e .

# Set up API key
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### Your First Investigation

```bash
# Start a new investigation
drama investigate "birthday cake incident"

# You'll be prompted for a summary, then interviewed
# The AI adapts questions based on your answers

# List all investigations
drama list

# Generate analysis report
drama analyze <session-id>

# Resume a paused investigation
drama resume <session-id>
```

## Example Usage

```
$ drama investigate "forgotten anniversary"

🔍 DRAMA DETECTIVE v1.0 🔍
Truth-seeking AI interviewer

Starting investigation: forgotten anniversary

First, give me a brief summary of what happened:
> My partner forgot our anniversary and I'm upset

⚙️  Analyzing situation and preparing questions...

Detective: Let's start with the timeline. When was your anniversary,
and when did you realize your partner had forgotten?

You: It was yesterday, October 15th. I realized in the morning when
they didn't mention it.

⚙️  Analyzing response...

Detective: How did you bring it up with your partner, or have you
discussed it yet?

[... interview continues ...]
```

After the interview, generate a report:

```
$ drama analyze abc-123

📊 ANALYSIS REPORT: forgotten anniversary

📅 TIMELINE OF EVENTS
──────────────────────────────────────────────────
   Oct 15th  Anniversary date
   Morning   User realized partner forgot
   Evening   User mentioned it, partner apologized

📋 KEY FACTS
──────────────────────────────────────────────────
• Partner has been stressed with work deadlines
• This is the first time partner forgot
• Partner immediately apologized and made plans

⚖️  VERDICT: Who's in the Wrong?
──────────────────────────────────────────────────

Primary responsibility: Partner (60%)
  Forgot important date despite reminders

Contributing factors: Both partners could improve communication (40%)

🎯 DRAMA RATING: 4/10
   🔥🔥🔥🔥······
   Low-moderate - Easily resolvable with conversation
```

## Technical Details

**Tech Stack:**
- Python 3.10+
- Anthropic Claude API (Sonnet 3.5)
- Click (CLI framework)
- Rich (terminal formatting)
- Pydantic (data validation)

**Multi-Agent System:**
1. **Goal Generator** - Creates investigation objectives from summary
2. **Fact Extractor** - Pulls structured claims from responses
3. **Drift Detector** - Identifies when answers go off-topic
4. **Goal Tracker** - Updates confidence scores for objectives
5. **Question Generator** - Creates contextually relevant questions
6. **Analysis Agent** - Synthesizes findings into reports

**State Management:**
- Sessions saved as JSON files in `~/.drama_detective/sessions/`
- Supports pause/resume at any point
- Full conversation history maintained

## Development

```bash
# Run tests
pytest

# Run specific test file
pytest tests/test_agents/test_goal_generator.py -v

# Install in development mode
pip install -e .
```

## Why I Built This

This project demonstrates the multi-agent AI patterns used in production systems like Fractional AI's Superintelligent. The core challenges—adaptive conversation flow, drift detection, question sequencing, and structured synthesis—are the same whether you're investigating drama or qualifying enterprise leads.

I built this as part of exploring conversational AI architecture and LLM orchestration, areas I'm passionate about and want to work on professionally.

## Future Enhancements

- Multi-subject interviews with contradiction detection
- Voice interface using speech-to-text
- Export reports as PDF/HTML
- Evaluation metrics for interview quality
- Integration with chat platforms (Slack, Discord)

## License

MIT

## Acknowledgments

Inspired by [Fractional AI's Superintelligent case study](https://www.fractional.ai/work/superintelligent) and the challenges of building adaptive conversational agents.
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
- Modify: `drama_detective/cli.py` (add version info)

**Step 1: Add version to CLI**

File: `drama_detective/cli.py` - Update the `cli` group:

```python
@click.group()
@click.version_option(version="1.0.0", prog_name="Drama Detective")
def cli():
    """🔍 Drama Detective - AI-powered drama investigation tool

    Start investigating with: drama investigate "incident name"
    """
    pass
```

**Step 2: Create example transcript**

File: `examples/demo_transcript.md`

```markdown
# Demo Investigation Transcript

## Incident: Birthday Cake Disaster

**Summary:** Sarah was supposed to bring a cake to Jordan's birthday party but forgot it.

### Interview Transcript

**Detective:** Let's start with the timeline. What time was the party supposed to start, and when did everyone realize the cake was missing?

**User:** The party was supposed to start at 5pm. We realized around 5:15pm when we were setting up the table that there was no cake.

**Detective:** You mentioned Sarah was responsible for the cake. How was that responsibility established - was it discussed in advance?

**User:** Yes, in our group chat three days before, Sarah volunteered to handle the cake when Jordan mentioned wanting a chocolate one.

**Detective:** When you realized the cake was missing at 5:15pm, did anyone try to contact Sarah, and what was her response?

**User:** Jordan texted her asking where she was. Sarah replied she was running late but didn't mention the cake at all.

**Detective:** What time did Sarah actually arrive, and what happened when the cake situation was brought up?

**User:** She showed up around 5:45pm without the cake. When asked about it, she said she "thought someone else was bringing it" even though we showed her the group chat where she volunteered.

**Detective:** How did Jordan and the other guests react to this explanation?

**User:** Jordan was clearly upset but tried to hide it. We ended up ordering pizza instead, but the mood was definitely affected. A few people left early.

**Detective:** Has Sarah acknowledged her mistake or apologized since the party?

**User:** She sent a text the next day saying she was "sorry for the confusion" but blamed it on having a busy week.

**Detective:** Is there anything else you'd like to add about this incident that we haven't covered?

**User:** I think it bothered everyone that she didn't just own up to forgetting. The excuse-making made it worse.

### Analysis Report

**Timeline:**
- 3 days before party: Sarah volunteers to bring chocolate cake
- 5:00pm: Party starts
- 5:15pm: Group realizes no cake
- 5:15pm: Jordan texts Sarah
- 5:45pm: Sarah arrives without cake, claims she thought someone else was bringing it
- Next day: Sarah sends apology text blaming busy week

**Key Facts:**
- Sarah clearly volunteered in group chat (documented)
- Sarah was 45 minutes late
- Sarah gave conflicting excuses (thought someone else had it vs. busy week)
- Jordan visibly upset, guests left early
- Sarah didn't take full responsibility

**Verdict:**
- **Primary Responsibility:** Sarah (85%)
  - Explicitly volunteered for task
  - Failed to communicate any issues beforehand
  - Gave conflicting, defensive excuses
  - Weak apology that shifted blame

- **Contributing Factors:** Group (15%)
  - Could have confirmed with Sarah day-of
  - Should have had backup plan for important item

**Drama Rating:** 7/10
- High - Damaged trust and relationships
- Made worse by excuse-making rather than genuine apology
- Requires honest conversation to repair
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
git add examples/demo_transcript.md drama_detective/cli.py
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

## Next Steps

**Day 7 Activities (not in this plan):**
- Record demo video/GIF
- Add personality/humor to agent prompts
- Test with real drama scenarios
- Refine prompts based on actual behavior
- Create portfolio-ready presentation
- Write blog post about architecture decisions

**Future Enhancements:**
- Multi-subject interview support
- Contradiction detection between accounts
- Voice interface
- Web UI
- Export to PDF/HTML

---

**Plan complete! Start execution with Task 1.**
