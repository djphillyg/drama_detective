# Drama Detective - Current Functionality

**Last Updated:** October 27, 2025
**Status:** Core functionality implemented and operational

---

## Overview

Drama Detective is an interactive CLI investigation tool that uses a **multi-agent AI system** to analyze interpersonal drama through structured interviews. The system conducts intelligent interviews, extracts facts, tracks investigation goals, and generates comprehensive analysis reports with drama ratings.

---

## Core Features

### 1. Multi-Agent Architecture (6 Specialized Agents)

Each agent has a specific role in the investigation pipeline:

- **Goal Generator Agent** (`goal_generator.py`)
  - Creates investigation objectives from initial incident summary
  - Generates structured goals with status tracking
  - Sets initial confidence scores

- **Question Generator Agent** (`question_generator.py`)
  - Generates contextual interview questions based on current state
  - Creates 4 multiple-choice answers with reasoning for each option
  - Adapts questions based on goals, facts, and conversation history
  - Handles drift redirect suggestions
  - Determines when investigation is complete (wrap_up signal)

- **Fact Extractor Agent** (`fact_extractor.py`)
  - Extracts concrete, verifiable claims from user responses
  - Categorizes facts by topic
  - Assigns timestamps and confidence levels ("certain" or "uncertain")
  - Tracks source attribution

- **Drift Detector Agent** (`drift_detector.py`)
  - Monitors if user answers stay on-topic
  - Runs every 3 turns to check for conversational drift
  - Provides redirect suggestions when answers go off-topic
  - Returns addressed_question boolean and redirect_suggestion text

- **Goal Tracker Agent** (`goal_tracker.py`)
  - Updates goal confidence scores (0-100) based on newly extracted facts
  - Marks goals as complete when sufficient information gathered
  - Tracks investigation progress dynamically

- **Analysis Agent** (`agent_analysis.py`)
  - Synthesizes all gathered data into final verdict
  - Generates timeline of events
  - Identifies key facts and unanswered questions
  - Assigns primary responsibility with percentage
  - Rates drama on 1-10 scale with explanation

---

## CLI Commands

### `drama investigate <incident_name>`
**Status:** ✅ Fully Implemented

Starts a new investigation with the following flow:

1. **Opens editor** for user to enter incident summary (multi-line support)
2. **Removes comment lines** (lines starting with #)
3. **Generates investigation goals** using Goal Generator Agent
4. **Presents first question** with multiple-choice answers (A, B, C, D, etc.)
5. **Starts interview loop:**
   - User selects answer by letter (A/B/C/D) or custom option
   - If custom answer selected, prompts for free-text input
   - Processes answer through agent pipeline:
     - Extracts facts
     - Checks for drift (every 3 turns)
     - Updates goal confidence scores
     - Generates next question
   - Saves session after each turn
   - Continues until investigation complete
6. **Automatically triggers analysis** when interview complete

**Features:**
- Multi-line incident summary via editor
- Letter-based answer selection (A, B, C, D...)
- Custom answer option (labeled "Other")
- Auto-save after each turn
- Progress tracking via turn count
- Session persistence throughout interview

### `drama list`
**Status:** ✅ Fully Implemented

Lists all investigation sessions in a formatted table:

**Table Columns:**
- **ID** - First 8 characters of session UUID
- **Incident** - Incident name
- **Status** - Color-coded (ACTIVE/PAUSED/COMPLETE)
  - Green = complete
  - Yellow = active
  - Blue = paused
- **Progress** - Average goal confidence percentage
- **Created** - Creation date (YYYY-MM-DD format)

**Additional Info:**
- Total session count
- Help text for resuming sessions
- Empty state message if no sessions exist

### `drama analyze <session_id>`
**Status:** ✅ Fully Implemented

Generates and displays comprehensive analysis report:

**Report Sections:**

1. **Timeline of Events**
   - Chronological reconstruction from gathered facts
   - Time and event description for each entry

2. **Key Facts Established**
   - Bullet list of verified information
   - Extracted from all user responses

3. **Unanswered Questions** (if any)
   - Gaps in the investigation
   - Questions that remain unclear

4. **The Verdict**
   - Primary responsibility assignment with percentage
   - Detailed reasoning
   - Contributing factors

5. **Drama Rating**
   - Numeric score (1-10)
   - Visual bar with fire emojis (🔥)
   - Explanation of rating

**Formatting:**
- Rich terminal colors and styling
- Panel borders with magenta theme
- Emoji indicators for each section
- Clear visual hierarchy

### `drama resume <session_id>`
**Status:** ⚠️ Not Yet Implemented

Placeholder exists but no functionality implemented.

---

## Data Models (Pydantic)

### Session
- `session_id`: UUID string
- `incident_name`: User-provided name
- `created_at`: ISO timestamp
- `status`: ACTIVE | PAUSED | COMPLETE
- `summary`: Initial incident description
- `goals`: List of Goal objects
- `messages`: Conversation history (Message objects)
- `facts`: Extracted facts (Fact objects)
- `answers`: Current multiple-choice options (Answer objects)
- `current_question`: Currently displayed question
- `turn_count`: Number of Q&A exchanges

### Goal
- `description`: Goal text
- `status`: NOT_STARTED | IN_PROGRESS | COMPLETE
- `confidence`: Integer 0-100 (auto-clamped)

### Fact
- `topic`: Category/subject
- `claim`: The actual fact statement
- `source`: Attribution (default: "user")
- `timestamp`: Optional time reference
- `confidence`: "certain" or "uncertain"

### Message
- `role`: "assistant" or "user"
- `content`: Message text
- `timestamp`: ISO timestamp

### Answer
- `answer`: Answer text
- `reasoning`: Why this answer might be chosen

---

## Session Management

### SessionManager Class (`session.py`)

**Functionality:**
- Creates unique session IDs (UUID4)
- Saves sessions as JSON files
- Loads sessions from disk
- Lists all sessions sorted by creation date
- Handles corrupted file gracefully (skips them)

**Storage Location:**
- Default: `.drama/.sessions/` in project root
- Customizable via `data_dir` parameter
- Auto-creates directories if missing

**File Format:**
- JSON serialization via Pydantic `model_dump()`
- Filename: `{session_id}.json`
- Human-readable with 2-space indentation

---

## Interview Orchestration

### InterviewOrchestrator Class (`interview.py`)

**Responsibilities:**
- Coordinates all 6 agents in sequence
- Manages interview state and flow
- Tracks turn count
- Determines completion status

**Agent Pipeline per Turn:**
1. Add user message to history
2. Extract facts from answer
3. Check for drift (every 3rd turn)
4. Update goal confidence scores
5. Generate next question with answers
6. Check if investigation complete
7. Add assistant message to history

**Session Isolation:**
- Each orchestrator stores `session_id`
- Passes session_id to all agent calls for context isolation

---

## API Integration

### ClaudeClient (`api_client.py`)

- Wraps Anthropic Claude API
- Provides unified interface for all agents
- Handles API key management
- Supports system prompts and message history
- Returns parsed JSON responses from agents

---

## User Interface

### Terminal Formatting (Rich Library)

**Components Used:**
- **Panel** - Bordered boxes for headers
- **Table** - Session listing
- **Console** - Colored output and input
- **Prompt** - Validated user input with choices

**Theme:**
- Primary: Magenta borders
- Accent: Cyan text
- Status colors: Green (complete), Yellow (active), Red (responsibility)
- Emojis: 🕵️ (detective), 🔥 (drama), ⚖️ (verdict), ⏰ (timeline)

**Input Methods:**
- `click.edit()` - Multi-line editor for incident summary
- `Prompt.ask()` - Letter-based answer selection with validation
- `console.input()` - Custom answer text entry

---

## Technical Features

### Type Safety
- Full Pydantic validation for all data structures
- Field validators (e.g., confidence clamping 0-100)
- Type hints throughout codebase

### Error Handling
- Empty summary validation
- File not found handling for sessions
- Corrupted JSON file resilience
- Empty answer validation

### State Management
- Conversation history tracking
- Persistent session storage
- Turn counting
- Status transitions (ACTIVE → COMPLETE)

### Context Isolation
- Session ID passed to all agents
- Prevents cross-contamination between investigations
- Enables session resumption architecture

---

## Test Coverage

Tests exist for:
- API client functionality
- All 6 agents (question generator, drift detector, fact extractor, goal tracker, goal generator, analysis)
- Interview orchestrator
- Session management (create, save, load, list)
- Data models validation

---

## Known Limitations

1. **Resume functionality not implemented** - CLI command exists but has no logic
2. **No edit/delete session commands** - Can only create and view
3. **No export functionality** - Analysis only displayed in terminal
4. **Fixed interview length** - Agent determines completion, no manual override
5. **No mid-interview analysis** - Only available after completion
6. **Single-user sessions** - No multi-participant interviews

---

## Dependencies

- **Python 3.9+** - Core language
- **Anthropic SDK** - Claude API access
- **Pydantic** - Data validation
- **Rich** - Terminal formatting
- **Click** - CLI framework
- **pytest** - Testing framework

---

## File Structure

```
src/
├── agents/
│   ├── agent_analysis.py      # Final verdict generation
│   ├── drift_detector.py      # Off-topic detection
│   ├── fact_extractor.py      # Claim extraction
│   ├── goal_generator.py      # Objective creation
│   ├── goal_tracker.py        # Progress monitoring
│   └── question_generator.py  # Q&A generation
├── models.py                  # Pydantic data models
├── prompts.py                 # Agent system prompts
├── api_client.py              # Claude API wrapper
├── interview.py               # Agent orchestration
├── session.py                 # Session persistence
├── cli.py                     # CLI commands
└── report_formatter.py        # Analysis display

tests/
├── test_agents/               # Agent unit tests
├── test_api_client.py
├── test_interview.py
├── test_models.py
└── test_session.py

.drama/.sessions/              # Session storage (gitignored)
```

---

## Summary

**What Works:**
- Complete investigation flow from start to finish
- Multi-agent system with specialized roles
- Dynamic question generation based on conversation state
- Fact extraction and goal tracking
- Drift detection to keep conversations on-topic
- Session persistence and listing
- Comprehensive analysis reports with drama ratings
- Rich terminal UI with colors and formatting

**What's Missing:**
- Resume investigation functionality
- Session editing/deletion
- Export capabilities
- Manual investigation controls
- Multi-participant support

**Overall Status:** Core investigation functionality is complete and operational. The system can conduct full interviews from inception to final analysis report.
