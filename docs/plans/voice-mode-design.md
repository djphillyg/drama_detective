# Voice Mode Design Document

## Overview

This document outlines the design for adding a voice-based interview mode to Drama Detective using Hume EVI (Empathic Voice Interface). This will be a completely separate flow from the existing text-based CLI interview system.

### Key Principles

- **Separate Flow**: Voice mode is independent from existing text mode (CLI with multiple choice)
- **Persistent Connection**: Single continuous voice conversation, not start/stop per question
- **Autonomous Agent**: Voice agent tracks goals internally and decides when to conclude
- **Post-Processing**: Backend processes full transcript AFTER conversation ends
- **Feature Flagged**: Hidden behind feature flag initially for testing

---

## Architecture Comparison

### Existing Text Mode (Keep As-Is)
```
User → CLI/Frontend → Question Generator Agent
                    ↓
                    User selects multiple choice answer
                    ↓
                    Fact Extractor Agent
                    ↓
                    Goal Tracker Agent
                    ↓
                    Question Generator Agent (next question)
                    ↓
                    Repeat until goals > 80% confidence
                    ↓
                    Analysis Agent → Final Report
```

### New Voice Mode (Build This)
```
User → Frontend Voice Page → Hume EVI Call Starts
                            ↓
                            Voice Agent (autonomous conversation)
                            - Asks questions naturally
                            - Internally tracks goal confidence
                            - Decides when to conclude
                            ↓
                            Call Ends
                            ↓
                            Backend receives full transcript
                            ↓
                            Summary Extraction
                            ↓
                            Fact Extraction from transcript
                            ↓
                            Goal Generation & Confidence Calculation
                            ↓
                            Analysis Agent → Final Report
```

**Key Difference**: Text mode = sequential agent calls during interview. Voice mode = single agent during call, then batch processing after.

---

## Voice Agent Design

### Unified System Prompt

The voice agent must handle ALL interview responsibilities in a single prompt:

**Core Responsibilities:**
1. Greet user and build rapport
2. Understand the incident through open conversation
3. Extract information across 6 key areas (actors, timeline, trigger, actions, context, perspective)
4. Internally track confidence for each area (not shared with user)
5. Determine when enough information is gathered (80%+ across all areas)
6. Gracefully conclude the interview
7. Thank user and set expectations

**Internal Goal Tracking Mechanism:**

Agent mentally maintains confidence scores:
```
ACTORS: ___%
TIMELINE: ___%
TRIGGER: ___%
ACTIONS & REACTIONS: ___%
CONTEXT & BACKGROUND: ___%
USER'S PERSPECTIVE: ___%

Target: All areas 80%+ before concluding
```

After each user response, agent silently updates these scores and decides:
- Should I probe deeper here?
- Should I move to a different area?
- Do I have enough to wrap up?

**Conversation Structure:**

1. **Opening (1-2 min)**: Warm greeting, invite user to share story
2. **Deep Dive (5-8 min)**: Natural Q&A following conversation threads, probing gaps
3. **Wrap-up (1-2 min)**: Final opportunity for additions, thank you, set expectations

**Graceful Exit Strategy:**

When confidence goals are met:
1. Signal: "Okay, I think I'm getting a pretty complete picture..."
2. Final check: "Is there anything else you think I should know?"
3. Closure: "Thank you for sharing. I'll put together an analysis for you."
4. Natural goodbye

**Tone & Style:**
- Empathetic but professional
- Non-judgmental (no sides taken during interview)
- Curious and engaged
- Natural conversational flow
- Validating ("That sounds frustrating", "I can see why that hurt")

**See appendix for full system prompt template**

---

## Backend Architecture

### New Models/Types

```python
class VoiceSession(BaseModel):
    """Extended session model for voice interviews"""
    session_id: str
    mode: Literal["text", "voice"] = "voice"  # NEW: track interview mode
    hume_conversation_id: Optional[str] = None  # NEW: Hume's conversation ID
    voice_call_started_at: Optional[str] = None  # NEW: when call began
    voice_call_ended_at: Optional[str] = None  # NEW: when call ended
    voice_call_duration_seconds: Optional[int] = None  # NEW: call length
    # All existing Session fields inherited...
```

### API Endpoints

#### 1. Create Voice Session
```
POST /api/voice/sessions

Request:
{
  "incident_name": "optional-name",
  "user_metadata": {
    "user_id": "optional",
    "source": "web-app"
  }
}

Response:
{
  "session_id": "uuid-here",
  "hume_config_id": "drama-detective-config",
  "metadata": {
    "session_id": "uuid-here"  // Pass to Hume
  }
}
```

Purpose: Create session BEFORE Hume call starts, return metadata to pass to Hume

#### 2. Hume Webhook Handler
```
POST /webhooks/hume/events

Receives real-time events from Hume:
- conversation.started
- message.received (user spoke)
- message.sent (agent responded)
- conversation.ended
```

Event handling:
- `conversation.started`: Link Hume conversation ID to session
- `message.received/sent`: Append to session.messages in real-time (optional for monitoring)
- `conversation.ended`: Trigger full transcript processing

#### 3. Process Voice Completion
```
POST /api/voice/sessions/{session_id}/process

Triggered by conversation.ended webhook

Processing pipeline:
1. Load full transcript from session.messages
2. Run summary extraction on transcript
3. Generate investigation goals
4. Extract facts from transcript
5. Calculate goal confidence scores
6. Mark session as complete
7. Generate analysis
8. Return analysis

Response:
{
  "status": "complete",
  "session_id": "uuid",
  "analysis_ready": true
}
```

#### 4. Get Voice Session Status
```
GET /api/voice/sessions/{session_id}

Response:
{
  "session_id": "uuid",
  "status": "active" | "processing" | "complete",
  "call_duration_seconds": 482,
  "message_count": 24,
  "analysis": { ... } // Only present when status=complete
}
```

Purpose: Frontend polls this during "Processing..." phase

### Webhook Event Handlers

```python
# backend/src/webhooks/hume.py

@router.post("/webhooks/hume/events")
async def handle_hume_event(event: HumeWebhookEvent):
    """
    Real-time webhook receiver for Hume conversation events
    """

    if event.type == "conversation.started":
        # Link Hume conversation to our session
        session_id = event.metadata.get("session_id")
        session = session_manager.load_session(session_id)
        session.hume_conversation_id = event.conversation_id
        session.voice_call_started_at = event.timestamp
        session.status = SessionStatus.ACTIVE
        session_manager.save_session(session)

    elif event.type == "message.received":
        # User spoke - append to transcript
        session_id = extract_session_id(event)
        session = session_manager.load_session(session_id)
        session.messages.append(Message(
            role="user",
            content=event.message.transcript,
            timestamp=event.timestamp
        ))
        session_manager.save_session(session)

    elif event.type == "message.sent":
        # Agent spoke - append to transcript
        session_id = extract_session_id(event)
        session = session_manager.load_session(session_id)
        session.messages.append(Message(
            role="assistant",
            content=event.message.text,
            timestamp=event.timestamp
        ))
        session_manager.save_session(session)

    elif event.type == "conversation.ended":
        # Call ended - trigger processing
        session_id = extract_session_id(event)
        session = session_manager.load_session(session_id)
        session.voice_call_ended_at = event.timestamp
        session.voice_call_duration_seconds = calculate_duration(
            session.voice_call_started_at,
            session.voice_call_ended_at
        )
        session_manager.save_session(session)

        # Trigger async processing pipeline
        await process_voice_completion(session_id)

    return {"status": "received"}
```

### Post-Conversation Processing Pipeline

```python
# backend/src/voice_processor.py

async def process_voice_completion(session_id: str):
    """
    Full pipeline to process completed voice interview.
    Called after conversation.ended webhook.
    """
    session = session_manager.load_session(session_id)

    # Mark as processing
    session.status = SessionStatus.PROCESSING
    session_manager.save_session(session)

    try:
        # 1. Build full transcript
        transcript = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in session.messages
        ])

        # 2. Extract summary from transcript
        summary_extractor = SummaryExtractorAgent(claude_client)
        extracted_summary = summary_extractor.extract_summary(
            summary_text=transcript,  # Use transcript as "summary"
            image_data_list=[],
            session_id=session_id
        )
        session.extracted_summary = extracted_summary

        # 3. Generate investigation goals
        goal_generator = GoalGeneratorAgent(claude_client)
        goals = goal_generator.generate_goals(
            extracted_summary,
            session_id=session_id
        )
        session.goals = goals

        # 4. Extract facts from full transcript
        fact_extractor = FactExtractorAgent(claude_client)
        facts = fact_extractor.extract_from_transcript(
            transcript,
            session_id=session_id
        )
        session.facts = facts

        # 5. Calculate goal confidence based on extracted facts
        goal_tracker = GoalTrackerAgent(claude_client)
        updated_goals = goal_tracker.calculate_final_confidence(
            goals,
            facts,
            session_id=session_id
        )
        session.goals = updated_goals

        # 6. Generate final analysis
        analysis_agent = AnalysisAgent(claude_client)
        analysis = analysis_agent.generate_analysis(
            session.model_dump(),
            session_id=session_id
        )
        session.analysis = analysis  # Store analysis in session

        # 7. Mark complete
        session.status = SessionStatus.COMPLETE
        session_manager.save_session(session)

        # 8. Notify user (optional: email, webhook, etc.)
        # await notify_user_analysis_ready(session_id)

    except Exception as e:
        session.status = SessionStatus.FAILED
        session.error = str(e)
        session_manager.save_session(session)
        raise
```

---

## Frontend Architecture

### New Route: Voice Interview Page

```
/voice-interview (feature flagged)
```

### Component Hierarchy

```
VoiceInterviewPage
├── VoiceInterviewContainer
│   ├── PreCallSetup (initial state)
│   ├── ActiveCall (Hume connected)
│   ├── Processing (call ended, analysis running)
│   └── Results (analysis complete)
```

### Component Details

#### VoiceInterviewPage.tsx
```typescript
export default function VoiceInterviewPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<'setup' | 'calling' | 'processing' | 'complete'>('setup');

  // Feature flag check
  const { isEnabled } = useFeatureFlag('voice-mode');
  if (!isEnabled) {
    return <Navigate to="/" />;
  }

  return (
    <div className="voice-interview-page">
      {status === 'setup' && <PreCallSetup onStart={handleStart} />}
      {status === 'calling' && <ActiveCall sessionId={sessionId} onEnd={handleEnd} />}
      {status === 'processing' && <Processing sessionId={sessionId} onComplete={handleComplete} />}
      {status === 'complete' && <Results sessionId={sessionId} />}
    </div>
  );
}
```

#### PreCallSetup.tsx
```typescript
// Initial screen before call starts
export function PreCallSetup({ onStart }) {
  const [incidentName, setIncidentName] = useState('');

  const startInterview = async () => {
    // Create session
    const response = await fetch('/api/voice/sessions', {
      method: 'POST',
      body: JSON.stringify({
        incident_name: incidentName || `voice-${Date.now()}`
      })
    });
    const { session_id, hume_config_id, metadata } = await response.json();

    onStart(session_id, metadata);
  };

  return (
    <div className="pre-call-setup">
      <h1>Voice Interview</h1>
      <input
        placeholder="Give this investigation a name (optional)"
        value={incidentName}
        onChange={e => setIncidentName(e.target.value)}
      />
      <button onClick={startInterview}>Start Interview</button>
    </div>
  );
}
```

#### ActiveCall.tsx
```typescript
// During live call with Hume
import { useVoice } from '@humeai/react';

export function ActiveCall({ sessionId, onEnd }) {
  const { status, messages, connect, disconnect } = useVoice({
    apiKey: process.env.REACT_APP_HUME_API_KEY,
    configId: 'drama-detective-interviewer',
    onMessage: (msg) => {
      // Real-time transcript display
      console.log('Message:', msg);
    },
    onDisconnect: () => {
      onEnd();
    }
  });

  useEffect(() => {
    // Auto-connect when component mounts
    connect({
      metadata: { session_id: sessionId }
    });
  }, []);

  return (
    <div className="active-call">
      <div className="status-indicator pulsing">
        🎙️ Interview in Progress
      </div>

      <div className="transcript">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : 'Detective'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>

      <button onClick={disconnect} className="end-call-btn">
        End Interview
      </button>
    </div>
  );
}
```

#### Processing.tsx
```typescript
// Shows loading state while backend processes transcript
export function Processing({ sessionId, onComplete }) {
  useEffect(() => {
    // Poll session status
    const interval = setInterval(async () => {
      const response = await fetch(`/api/voice/sessions/${sessionId}`);
      const session = await response.json();

      if (session.status === 'complete') {
        clearInterval(interval);
        onComplete(session);
      }
    }, 2000);  // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="processing">
      <Spinner />
      <h2>Analyzing Your Interview...</h2>
      <p>This usually takes 30-60 seconds</p>
    </div>
  );
}
```

#### Results.tsx
```typescript
// Display final analysis (reuse existing report component)
export function Results({ sessionId }) {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    fetch(`/api/voice/sessions/${sessionId}`)
      .then(r => r.json())
      .then(session => setAnalysis(session.analysis));
  }, [sessionId]);

  if (!analysis) return <Spinner />;

  return <AnalysisReport analysis={analysis} />;  // Reuse existing component
}
```

---

## Hume EVI Configuration

### Configuration Setup

1. **Create Hume Account**: Sign up at hume.ai
2. **Create EVI Configuration**:
   - Name: "Drama Detective Interviewer"
   - System Prompt: [Use unified voice agent prompt from appendix]
   - Voice: Choose empathetic, conversational voice
   - Language Model: Best available (GPT-4 or Claude via Hume)

3. **Configure Webhooks**:
   - Webhook URL: `https://your-domain.com/webhooks/hume/events`
   - Events to subscribe:
     - `conversation.started`
     - `message.received`
     - `message.sent`
     - `conversation.ended`

4. **Get Credentials**:
   - API Key (for frontend SDK)
   - Config ID (for referencing this specific configuration)

### Environment Variables

```bash
# Frontend (.env)
REACT_APP_HUME_API_KEY=your-hume-api-key
REACT_APP_HUME_CONFIG_ID=drama-detective-interviewer

# Backend (.env)
HUME_WEBHOOK_SECRET=your-webhook-secret  # For verifying webhook authenticity
```

---

## Feature Flag Implementation

### Backend Flag Check

```python
# backend/src/feature_flags.py

def is_voice_mode_enabled(user_id: Optional[str] = None) -> bool:
    """
    Check if voice mode is enabled.
    Initially: environment variable
    Later: database-driven per-user flags
    """
    return os.getenv("FEATURE_VOICE_MODE", "false").lower() == "true"
```

### Frontend Flag Component

```typescript
// frontend/src/hooks/useFeatureFlag.ts

export function useFeatureFlag(flagName: string) {
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    // Check environment variable or API
    const enabled = import.meta.env.VITE_FEATURE_VOICE_MODE === 'true';
    setIsEnabled(enabled);
  }, [flagName]);

  return { isEnabled };
}
```

### Conditional Navigation

```typescript
// Only show voice interview link if flag enabled
{isVoiceModeEnabled && (
  <Link to="/voice-interview">Try Voice Interview (Beta)</Link>
)}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: CALL INITIATION                                        │
└─────────────────────────────────────────────────────────────────┘
Frontend: User clicks "Start Interview"
    ↓
Frontend: POST /api/voice/sessions → Backend creates session
    ↓
Frontend: Receives session_id + metadata
    ↓
Frontend: Calls useVoice.connect({ metadata: { session_id } })
    ↓
Hume: Initiates voice call, sends webhook: conversation.started
    ↓
Backend: Links hume_conversation_id to session

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: ACTIVE CONVERSATION                                    │
└─────────────────────────────────────────────────────────────────┘
User speaks
    ↓
Hume: Transcribes → sends webhook: message.received
    ↓
Backend: Appends to session.messages
    ↓
Hume: Voice agent processes with system prompt
    ↓
Voice Agent: Responds naturally, tracks goals internally
    ↓
Hume: Sends webhook: message.sent
    ↓
Backend: Appends to session.messages
    ↓
[Repeat conversation loop]
    ↓
Voice Agent: Determines goals met → concludes gracefully
    ↓
User/Agent: Say goodbye

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: CALL END & PROCESSING                                  │
└─────────────────────────────────────────────────────────────────┘
Hume: Call ends → sends webhook: conversation.ended
    ↓
Backend: Marks call_ended_at, triggers process_voice_completion()
    ↓
Backend: Extract summary from full transcript
    ↓
Backend: Generate goals based on summary
    ↓
Backend: Extract facts from transcript
    ↓
Backend: Calculate goal confidence scores
    ↓
Backend: Generate analysis
    ↓
Backend: Mark session.status = COMPLETE
    ↓
Frontend: Polling detects status=complete
    ↓
Frontend: Display analysis results
```

---

## Testing Strategy

### Phase 1: Hume Configuration Testing
- Create Hume config with system prompt
- Test via Hume's web interface first
- Validate that agent:
  - Greets naturally
  - Asks follow-up questions
  - Tracks conversation mentally
  - Concludes appropriately

### Phase 2: Webhook Integration Testing
- Use ngrok or similar to expose local backend
- Configure Hume webhooks to local URL
- Test that webhooks are received and processed
- Verify transcript is being stored in real-time

### Phase 3: Frontend Integration Testing
- Build basic PreCallSetup → ActiveCall flow
- Test Hume SDK connection
- Verify metadata (session_id) is passed correctly
- Test call end detection

### Phase 4: End-to-End Testing
- Run full flow: Start call → Interview → End call
- Verify processing pipeline runs
- Confirm analysis is generated
- Check frontend displays results

### Phase 5: User Acceptance Testing
- Test with real drama scenarios
- Validate agent doesn't conclude too early or too late
- Assess quality of generated analysis
- Iterate on system prompt based on results

---

## Implementation Phases

### Phase 1: Backend Foundation (Week 1)
- [ ] Create VoiceSession model extension
- [ ] Build `/api/voice/sessions` endpoint
- [ ] Implement Hume webhook handler
- [ ] Build post-conversation processing pipeline
- [ ] Test with mock Hume events

### Phase 2: Hume Configuration (Week 1)
- [ ] Create Hume account and config
- [ ] Finalize voice agent system prompt
- [ ] Configure webhooks
- [ ] Test via Hume web interface
- [ ] Iterate on prompt based on test conversations

### Phase 3: Frontend Implementation (Week 2)
- [ ] Build VoiceInterviewPage route
- [ ] Implement PreCallSetup component
- [ ] Integrate Hume SDK in ActiveCall component
- [ ] Build Processing polling component
- [ ] Reuse existing Results/Analysis display

### Phase 4: Feature Flag & Integration (Week 2)
- [ ] Add feature flag environment variables
- [ ] Conditional route rendering
- [ ] End-to-end testing
- [ ] Deploy behind feature flag

### Phase 5: Iteration & Polish (Week 3)
- [ ] User testing with real scenarios
- [ ] Prompt refinement
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Documentation

---

## Appendix: Full Voice Agent System Prompt

```
[See prompts_voice.py - full system prompt template]

Key sections:
1. Role & Responsibilities
2. Internal Investigation Checklist (6 goal areas with confidence tracking)
3. Confidence Update Mechanism
4. Conclusion Criteria & Strategy
5. Conversation Structure (Opening/Deep Dive/Wrap-up)
6. Tone & Personality Guidelines
7. What NOT to do
8. Special Handling scenarios
```

---

## Open Questions

1. **Prompt Tuning**: How many test conversations needed before confident in prompt?
2. **Call Length**: Should we enforce maximum call duration (e.g., 15 min hard cutoff)?
3. **Error Handling**: What if Hume call fails mid-conversation? How to recover session?
4. **Transcript Quality**: Does Hume's transcription quality meet our needs? Any preprocessing required?
5. **Cost**: Hume EVI pricing per minute - what's acceptable cost per interview?
6. **Analytics**: What metrics should we track? (avg call duration, completion rate, agent conclusion accuracy)

---

## Success Criteria

Voice mode is considered successful when:
- [ ] Agent consistently gathers complete information (all 6 goal areas >75%)
- [ ] Agent concludes gracefully without user needing to manually end call
- [ ] Generated analysis quality matches or exceeds text mode
- [ ] Average call duration is 8-12 minutes
- [ ] User feedback indicates natural, empathetic conversation experience
- [ ] <5% technical failure rate (dropped calls, webhook issues, etc.)

---

## Future Enhancements (Post-MVP)

1. **Real-time Goal Monitoring**: Display goal confidence in frontend during call
2. **Multi-language Support**: Leverage Hume's language detection
3. **Emotion Analytics**: Use Hume's emotion detection in analysis
4. **Call Recording**: Option to play back audio
5. **Agent Coaching**: Allow users to provide feedback to improve future interviews
6. **Async Interviews**: Call ends, user can call back later to add more info