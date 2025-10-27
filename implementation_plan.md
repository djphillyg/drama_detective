# Drama Detective - Flask API + Next.js Frontend Implementation Plan

**Goal:** Build a mobile-first web interface with Flask REST API backend

**Deployment Target:** Railway (both frontend and backend)

---

## Phase 1: Flask REST API

### API Architecture

**Base URL:** `http://localhost:5000/api` (dev) / `https://drama-api.railway.app/api` (prod)

**Key Design Decisions:**
- Stateless API design (session state stored in backend, not client)
- CORS enabled for Next.js frontend
- JSON request/response format
- Error handling with consistent error response schema

---

### API Endpoints Specification

#### 1. POST `/api/investigate`
**Purpose:** Start a new investigation

**Request Body:**
```json
{
  "incident_name": "mexico-trip-drama",
  "summary": "John and Rob went to Mexico together, and Lamar got upset because Rob is his good friend and he wasn't invited."
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "incident_name": "mexico-trip-drama",
  "question": "Why did Lamar get upset about this?",
  "answers": [
    {"answer": "Because Rob is his good friend", "reasoning": "..."},
    {"answer": "Because he wasn't invited", "reasoning": "..."},
    {"answer": "Because John is his ex", "reasoning": "..."}
  ],
  "turn_count": 0,
  "goals": [
    {"description": "Understand relationship dynamics", "confidence": 0, "status": "not_started"}
  ]
}
```

**Backend Implementation:**
```python
@app.route('/api/investigate', methods=['POST'])
def investigate():
    data = request.json
    incident_name = data['incident_name']
    summary = data['summary']

    # Create session
    session_manager = SessionManager()
    session = session_manager.create_session(incident_name)

    # Initialize investigation
    orchestrator = InterviewOrchestrator(session)
    first_question = orchestrator.initialize_investigation(summary)

    # Save session
    session_manager.save_session(session)

    # Return response
    return jsonify({
        'session_id': session.session_id,
        'incident_name': session.incident_name,
        'question': session.current_question,
        'answers': [a.model_dump() for a in session.answers],
        'turn_count': session.turn_count,
        'goals': [g.model_dump() for g in session.goals]
    })
```

---

#### 2. POST `/api/answer`
**Purpose:** Submit answer and get next question

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "answer": {
    "answer": "Because Rob is his good friend",
    "reasoning": "This explains the relationship dynamic"
  }
}
```

**Response:**
```json
{
  "question": "How did Lamar find out about the trip?",
  "answers": [...],
  "is_complete": false,
  "turn_count": 1,
  "goals": [
    {"description": "Understand relationship dynamics", "confidence": 45, "status": "in_progress"}
  ],
  "facts_count": 3
}
```

**Or if interview complete:**
```json
{
  "is_complete": true,
  "session_id": "uuid-string",
  "message": "Interview complete. Proceed to analysis."
}
```

**Backend Implementation:**
```python
@app.route('/api/answer', methods=['POST'])
def submit_answer():
    data = request.json
    session_id = data['session_id']
    answer_data = data['answer']

    # Load session
    session_manager = SessionManager()
    session = session_manager.load_session(session_id)

    # Process answer
    orchestrator = InterviewOrchestrator(session)
    answer_obj = Answer(**answer_data)
    next_question, is_complete = orchestrator.process_answer(answer_obj)

    # Save session
    session_manager.save_session(session)

    if is_complete:
        return jsonify({
            'is_complete': True,
            'session_id': session_id,
            'message': 'Interview complete. Proceed to analysis.'
        })

    return jsonify({
        'question': next_question,
        'answers': [a.model_dump() for a in session.answers],
        'is_complete': False,
        'turn_count': session.turn_count,
        'goals': [g.model_dump() for g in session.goals],
        'facts_count': len(session.facts)
    })
```

---

#### 3. GET `/api/sessions`
**Purpose:** List all investigation sessions

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-1",
      "incident_name": "mexico-trip-drama",
      "status": "complete",
      "created_at": "2025-10-27T10:30:00",
      "turn_count": 8,
      "progress": 85
    },
    {
      "session_id": "uuid-2",
      "incident_name": "birthday-party-fiasco",
      "status": "active",
      "created_at": "2025-10-27T11:00:00",
      "turn_count": 3,
      "progress": 32
    }
  ]
}
```

**Backend Implementation:**
```python
@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()

    sessions_data = []
    for session in sessions:
        # Calculate progress
        if session.goals:
            avg_confidence = sum(g.confidence for g in session.goals) / len(session.goals)
        else:
            avg_confidence = 0

        sessions_data.append({
            'session_id': session.session_id,
            'incident_name': session.incident_name,
            'status': session.status.value,
            'created_at': session.created_at,
            'turn_count': session.turn_count,
            'progress': int(avg_confidence)
        })

    return jsonify({'sessions': sessions_data})
```

---

#### 4. GET `/api/analysis/<session_id>`
**Purpose:** Get analysis report for completed investigation

**Response:**
```json
{
  "incident_name": "mexico-trip-drama",
  "analysis": {
    "timeline": [
      {"time": "March 15", "event": "John and Rob planned Mexico trip"},
      {"time": "March 20", "event": "Lamar discovered the trip"}
    ],
    "key_facts": [
      "Rob and Lamar are close friends",
      "John and Rob went to Mexico without telling Lamar"
    ],
    "gaps": [
      "Was this an intentional exclusion?"
    ],
    "verdict": {
      "primary_responsibility": "Rob",
      "percentage": 60,
      "reasoning": "As Lamar's close friend, Rob should have communicated or invited him",
      "contributing_factors": "John may have influenced the decision",
      "drama_rating": 6,
      "drama_rating_explanation": "Moderate drama - friendship betrayal but not malicious"
    }
  }
}
```

**Backend Implementation:**
```python
@app.route('/api/analysis/<session_id>', methods=['GET'])
def get_analysis(session_id):
    session_manager = SessionManager()
    session = session_manager.load_session(session_id)

    # Generate analysis
    analysis_agent = AnalysisAgent(client=ClaudeClient())
    analysis = analysis_agent.generate_analysis(
        session.model_dump(),
        session_id=session_id
    )

    return jsonify({
        'incident_name': session.incident_name,
        'analysis': analysis
    })
```

---

### Flask App Structure

```
drama_detective/
├── src/
│   ├── agents/          # Existing agents
│   ├── api/             # NEW: Flask API
│   │   ├── __init__.py
│   │   ├── app.py       # Flask app initialization
│   │   ├── routes.py    # API endpoints
│   │   └── utils.py     # Helper functions
│   ├── models.py        # Existing Pydantic models
│   └── ...
├── requirements.txt     # Add flask, flask-cors
└── api_server.py        # NEW: Entry point for Flask
```

**requirements.txt additions:**
```
flask==3.0.0
flask-cors==4.0.0
```

**api_server.py:**
```python
from src.api.app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**src/api/app.py:**
```python
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://drama-detective.railway.app"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register routes
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
```

---

## Phase 2: Next.js Frontend

### Tech Stack
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** (for styling)
- **Custom terminal theme** (chalk-inspired colors)

### Project Structure

```
drama-detective-web/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Home page (start investigation)
│   │   ├── interview/
│   │   │   └── [sessionId]/
│   │   │       └── page.tsx      # Interview flow
│   │   ├── sessions/
│   │   │   └── page.tsx          # Sessions list
│   │   ├── analysis/
│   │   │   └── [sessionId]/
│   │   │       └── page.tsx      # Analysis report
│   │   └── layout.tsx            # Root layout
│   ├── components/
│   │   ├── Terminal.tsx          # Terminal-styled container
│   │   ├── QuestionCard.tsx      # Multiple choice question
│   │   ├── AnalysisReport.tsx    # Formatted analysis
│   │   └── SessionCard.tsx       # Session list item
│   ├── lib/
│   │   ├── api.ts                # API client
│   │   └── types.ts              # TypeScript types
│   └── styles/
│       └── terminal.css          # Terminal theme
├── public/
└── package.json
```

---

### Terminal Aesthetic Design

**Color Scheme (chalk-inspired):**
```css
:root {
  --terminal-bg: #1a1a1a;
  --terminal-text: #00ff00;      /* Green - classic terminal */
  --terminal-cyan: #00ffff;       /* Cyan - highlights */
  --terminal-yellow: #ffff00;     /* Yellow - warnings */
  --terminal-red: #ff0000;        /* Red - errors */
  --terminal-magenta: #ff00ff;    /* Magenta - accents */
  --terminal-dim: #808080;        /* Gray - dimmed text */
}
```

**Typography:**
```css
body {
  font-family: 'Courier New', monospace;
  background: var(--terminal-bg);
  color: var(--terminal-text);
}
```

**Mobile-First Design:**
- Full-width layout
- Touch-friendly buttons (min 44px height)
- No hover effects (use active states)
- Smooth scrolling for long content

---

### Page Designs

#### 1. Home Page (`/`)

**Layout:**
```
┌─────────────────────────────┐
│  🕵️ DRAMA DETECTIVE         │
│  ─────────────────────────  │
│                             │
│  > Start Investigation      │
│                             │
│  Incident Name:             │
│  [________________]          │
│                             │
│  Summary:                   │
│  [________________]          │
│  [________________]          │
│  [________________]          │
│                             │
│  [ BEGIN INVESTIGATION ]    │
│                             │
│  > View Past Cases          │
│                             │
└─────────────────────────────┘
```

**Component (page.tsx):**
```tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Terminal } from '@/components/Terminal'
import { startInvestigation } from '@/lib/api'

export default function HomePage() {
  const [incidentName, setIncidentName] = useState('')
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async () => {
    setLoading(true)
    const response = await startInvestigation(incidentName, summary)
    router.push(`/interview/${response.session_id}`)
  }

  return (
    <Terminal title="DRAMA DETECTIVE">
      <div className="space-y-4">
        <h1 className="text-terminal-cyan text-2xl">
          🕵️ DRAMA DETECTIVE
        </h1>

        <div className="border-t border-terminal-dim pt-4">
          <label className="text-terminal-text">
            {'> Incident Name:'}
          </label>
          <input
            type="text"
            value={incidentName}
            onChange={(e) => setIncidentName(e.target.value)}
            className="terminal-input"
            placeholder="mexico-trip-drama"
          />
        </div>

        <div>
          <label className="text-terminal-text">
            {'> Summary:'}
          </label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="terminal-input"
            rows={5}
            placeholder="Describe what happened..."
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="terminal-button"
        >
          {loading ? '[ LOADING... ]' : '[ BEGIN INVESTIGATION ]'}
        </button>

        <a href="/sessions" className="text-terminal-cyan">
          {'> View Past Cases'}
        </a>
      </div>
    </Terminal>
  )
}
```

---

#### 2. Interview Page (`/interview/[sessionId]`)

**Layout:**
```
┌─────────────────────────────┐
│  🕵️ mexico-trip-drama       │
│  Turn 3/? | Progress: 45%   │
│  ─────────────────────────  │
│                             │
│  > Why did Lamar get upset? │
│                             │
│  A) Because Rob is his      │
│     good friend             │
│                             │
│  B) Because he wasn't       │
│     invited                 │
│                             │
│  C) Because John is his ex  │
│                             │
│  D) [Custom answer...]      │
│                             │
│  [ SELECT ]                 │
│                             │
│  Goals:                     │
│  ▓▓▓▓▓░░░░░ 45% Understand  │
│                relationships│
└─────────────────────────────┘
```

**Component (page.tsx):**
```tsx
'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { QuestionCard } from '@/components/QuestionCard'
import { submitAnswer } from '@/lib/api'

export default function InterviewPage({ params }: { params: { sessionId: string } }) {
  const [questionData, setQuestionData] = useState(null)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const router = useRouter()

  const handleSubmit = async () => {
    const response = await submitAnswer(params.sessionId, selectedAnswer)

    if (response.is_complete) {
      router.push(`/analysis/${params.sessionId}`)
    } else {
      setQuestionData(response)
      setSelectedAnswer(null)
    }
  }

  return (
    <QuestionCard
      question={questionData.question}
      answers={questionData.answers}
      goals={questionData.goals}
      turnCount={questionData.turn_count}
      onSelect={setSelectedAnswer}
      onSubmit={handleSubmit}
    />
  )
}
```

---

#### 3. Sessions List Page (`/sessions`)

**Layout:**
```
┌─────────────────────────────┐
│  🕵️ PAST INVESTIGATIONS     │
│  ─────────────────────────  │
│                             │
│  [#abc123]                  │
│  mexico-trip-drama          │
│  Status: COMPLETE           │
│  Progress: 85% | 8 turns    │
│  2025-10-27                 │
│  [ VIEW ANALYSIS ]          │
│                             │
│  [#def456]                  │
│  birthday-party-fiasco      │
│  Status: ACTIVE             │
│  Progress: 32% | 3 turns    │
│  2025-10-27                 │
│  [ CONTINUE ]               │
│                             │
└─────────────────────────────┘
```

---

#### 4. Analysis Report Page (`/analysis/[sessionId]`)

**Layout:**
```
┌─────────────────────────────┐
│  🕵️ FINAL ANALYSIS          │
│  mexico-trip-drama          │
│  ─────────────────────────  │
│                             │
│  ⏰ TIMELINE                │
│  Mar 15: Trip planned       │
│  Mar 20: Lamar found out    │
│                             │
│  📋 KEY FACTS               │
│  • Rob and Lamar are close  │
│  • No invitation extended   │
│                             │
│  ⚖️ THE VERDICT             │
│  Primary: Rob (60%)         │
│  Reasoning: As Lamar's      │
│  close friend, Rob should   │
│  have communicated...       │
│                             │
│  🔥 DRAMA RATING            │
│  6/10                       │
│  🔥🔥🔥🔥🔥🔥⬜⬜⬜⬜          │
│  Moderate friendship drama  │
│                             │
│  [ START NEW INVESTIGATION ]│
└─────────────────────────────┘
```

---

### API Client (`lib/api.ts`)

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'

export async function startInvestigation(incidentName: string, summary: string) {
  const response = await fetch(`${API_BASE_URL}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_name: incidentName, summary })
  })
  return response.json()
}

export async function submitAnswer(sessionId: string, answer: any) {
  const response = await fetch(`${API_BASE_URL}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answer })
  })
  return response.json()
}

export async function getSessions() {
  const response = await fetch(`${API_BASE_URL}/sessions`)
  return response.json()
}

export async function getAnalysis(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/analysis/${sessionId}`)
  return response.json()
}
```

---

## Phase 3: Railway Deployment

### Backend Deployment

**railway.json:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python api_server.py"
  }
}
```

**Environment Variables:**
- `ANTHROPIC_API_KEY` (Claude API key)
- `PORT` (Railway auto-assigns)

### Frontend Deployment

**Environment Variables:**
- `NEXT_PUBLIC_API_URL` (Flask API URL from Railway)

---

## Testing Strategy

### Backend Testing
```bash
# Test investigate endpoint
curl -X POST http://localhost:5000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"incident_name": "test", "summary": "A and B had a fight"}'

# Test answer endpoint
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "answer": {"answer": "test", "reasoning": "test"}}'
```

### Frontend Testing
1. Run locally: `npm run dev`
2. Test on mobile: Use ngrok or Railway preview
3. Test full flow: Start → Interview → Analysis

---

## Implementation Order

1. ✅ Design API endpoints (this document)
2. Build Flask API structure
3. Implement each endpoint one by one
4. Test with curl/Postman
5. Initialize Next.js project
6. Build terminal UI components
7. Implement each page
8. Connect pages to API
9. Test end-to-end locally
10. Deploy to Railway (backend first, then frontend)
11. Test on mobile device

---

## Next Steps

Ready to start building! First task: Create Flask API structure.

Would you like me to:
1. Start implementing the Flask API now?
2. Review/adjust the plan first?
3. Something else?
