# Drama Detective CLI - 7-Day Build Plan

## Project Overview
Build a CLI-based "Drama Detective" that investigates friend group drama using adaptive AI interviews. This project demonstrates multi-agent architecture, LLM orchestration, and conversational state management - mirroring Fractional AI's Superintelligent voice agent case study.

**Core Architecture**: Multi-agent system with primary interviewer, drift detector, next-question selector, and synthesis agent.

**Tech Stack**: Python, OpenAI/Anthropic API, CLI interface (click/typer), simple file-based persistence

---

## Day 1: Foundation - Basic CLI Structure & Single Interview Flow

### Objectives
1. Set up project structure and dependencies
2. Create basic CLI interface with commands
3. Implement single-turn interview conversation with LLM
4. Save interview transcripts to files

### Pseudocode
```
# CLI Setup
create_cli_app():
    define command: "drama investigate <incident_name>"
    define command: "drama list"
    define command: "drama analyze <session_id>"

# Basic Interview Flow
start_interview(incident_name, interviewee_name):
    initialize session with unique ID
    create system prompt for interviewer agent
    
    while not interview_complete:
        get user input (simulating interviewee response)
        send to LLM with conversation history
        display agent's next question
        append to transcript
    
    save transcript to file with session_id

# Transcript Storage
save_transcript(session_id, transcript):
    create JSON file with:
        - session_id
        - incident_name
        - interviewee_name
        - timestamp
        - messages array [{role, content, timestamp}]
```

**Deliverables**: Working CLI that can conduct one interview and save it

---

## Day 2: Enhanced Interview Logic & Context Management

### Objectives
1. Implement conversation history management
2. Add goal-oriented questioning (extract specific facts)
3. Create better system prompts for natural flow
4. Add session pause/resume capability

### Pseudocode
```
# Enhanced Interviewer Agent
class InterviewAgent:
    def __init__(incident_name, interviewee_name, investigation_goals):
        self.context_window = []
        self.facts_gathered = []
        self.goals = investigation_goals  # ["get timeline", "understand who was present", etc.]
    
    def generate_question(user_response):
        # Add user response to context
        update_context(user_response)
        extract_facts(user_response)
        
        # Build prompt with:
        # - Investigation goals
        # - Facts gathered so far
        # - Recent conversation history
        prompt = build_prompt(self.goals, self.facts_gathered, self.context_window)
        
        question = call_llm(prompt)
        update_context(question)
        return question
    
    def extract_facts(response):
        # Use LLM to pull out concrete facts
        facts_prompt = "Extract factual claims from: {response}"
        new_facts = call_llm(facts_prompt)
        self.facts_gathered.append(new_facts)

# Session Management
resume_session(session_id):
    load transcript from file
    reconstruct context_window
    reconstruct facts_gathered
    continue interview loop

pause_session(session_id):
    save current state to file
    display "Session paused. Resume with: drama resume <session_id>"
```

**Deliverables**: Interview agent that remembers context and extracts facts

---

## Day 3: Multi-Agent Architecture - Drift Detector

### Objectives
1. Implement drift detection sub-agent
2. Add course correction when conversation goes off-track
3. Create question-specific goals system
4. Track conversation focus over time

### Pseudocode
```
# Drift Detection Agent
class DriftDetector:
    def __init__(investigation_goals, current_question_goal):
        self.investigation_goals = investigation_goals
        self.current_focus = current_question_goal
    
    def check_for_drift(recent_messages):
        # Analyze last 3-5 messages
        drift_prompt = f"""
        Investigation goal: {self.current_focus}
        Recent conversation: {recent_messages}
        
        Is the conversation still focused on the goal? 
        Return: {{on_track: bool, drift_reason: string, suggested_redirect: string}}
        """
        
        analysis = call_llm(drift_prompt, json_mode=True)
        return analysis
    
    def get_redirect_prompt(drift_analysis):
        return f"Let's get back on track. {drift_analysis.suggested_redirect}"

# Modified Interview Loop
start_interview_with_drift_detection():
    interviewer = InterviewAgent(...)
    drift_detector = DriftDetector(...)
    
    while not complete:
        user_response = get_input()
        
        # Check for drift every N turns
        if turn_count % 3 == 0:
            drift_analysis = drift_detector.check_for_drift(recent_messages)
            
            if not drift_analysis.on_track:
                display "[Drift detected: {drift_analysis.drift_reason}]"
                next_question = drift_analysis.suggested_redirect
            else:
                next_question = interviewer.generate_question(user_response)
        else:
            next_question = interviewer.generate_question(user_response)
        
        display next_question
```

**Deliverables**: Drift detection that keeps conversations on track

---

## Day 4: Next-Question Agent & Intelligent Question Sequencing

### Objectives
1. Build agent that selects next best question based on context
2. Implement question rewording to avoid repetition
3. Track which investigation goals have been addressed
4. Know when to end the interview

### Pseudocode
```
# Next Question Agent
class NextQuestionAgent:
    def __init__(investigation_goals):
        self.goals = investigation_goals
        self.goal_status = {goal: "not_started" for goal in goals}
        self.questions_asked = []
    
    def select_next_question(transcript, facts_gathered):
        # Determine which goals need more info
        incomplete_goals = [g for g in self.goals if self.goal_status[g] != "complete"]
        
        if not incomplete_goals:
            return None, "interview_complete"
        
        # Ask LLM to suggest next question
        selection_prompt = f"""
        Facts gathered: {facts_gathered}
        Incomplete goals: {incomplete_goals}
        Previous questions: {self.questions_asked}
        
        What should I ask next? Consider:
        - Which goal has the least information
        - What contradictions need clarification
        - What natural follow-ups exist from their last response
        
        Return: {{goal: string, question: string, reasoning: string}}
        """
        
        decision = call_llm(selection_prompt, json_mode=True)
        
        # Reword question to reference prior conversation
        reworded = self.reword_question(decision.question, transcript)
        
        self.questions_asked.append(reworded)
        return reworded, decision.goal
    
    def reword_question(question, transcript):
        reword_prompt = f"""
        Planned question: {question}
        Conversation so far: {transcript[-5:]}  # last 5 turns
        
        Reword the question to flow naturally from what was just discussed.
        Reference their previous answers when relevant.
        """
        return call_llm(reword_prompt)
    
    def mark_goal_complete(goal):
        self.goal_status[goal] = "complete"

# Integration with Main Flow
interview_with_intelligent_sequencing():
    interviewer = InterviewAgent(...)
    next_q_agent = NextQuestionAgent(investigation_goals)
    
    while not complete:
        user_response = get_input()
        interviewer.process_response(user_response)
        
        next_question, active_goal = next_q_agent.select_next_question(
            transcript, 
            interviewer.facts_gathered
        )
        
        if next_question is None:
            display "Thanks for your time! That covers everything."
            break
```

**Deliverables**: Smart question sequencing that knows what to ask next

---

## Day 5: Multiple Interview Subjects & Cross-Reference

### Objectives
1. Support interviewing multiple people about same incident
2. Store and organize multi-subject transcripts
3. Create framework for comparing accounts
4. Build simple CLI for managing multiple interviews

### Pseudocode
```
# Multi-Subject Investigation
class Investigation:
    def __init__(incident_name, subjects_list):
        self.incident_name = incident_name
        self.investigation_id = generate_uuid()
        self.subjects = subjects_list
        self.interviews = {}  # {subject_name: interview_session}
        self.all_facts = {}   # {subject_name: [facts]}
    
    def interview_subject(subject_name):
        print(f"\n--- Starting interview with {subject_name} ---")
        
        # Load facts from previous interviews for context
        existing_facts = self.get_facts_from_other_subjects(subject_name)
        
        # Create goals that include verifying others' claims
        goals = generate_investigation_goals(existing_facts)
        
        session = InterviewAgent(self.incident_name, subject_name, goals)
        transcript = session.conduct_interview()
        
        self.interviews[subject_name] = transcript
        self.all_facts[subject_name] = session.facts_gathered
        
        save_investigation_state(self)
    
    def get_facts_from_other_subjects(exclude_subject):
        other_facts = []
        for subject, facts in self.all_facts.items():
            if subject != exclude_subject:
                other_facts.extend(facts)
        return other_facts

# CLI Commands
drama investigate <incident> --subjects alex,sarah,jordan
    -> creates investigation
    -> interviews each subject sequentially
    -> saves all transcripts

drama interview <investigation_id> <subject_name>
    -> add another subject to existing investigation

drama subjects <investigation_id>
    -> list all interview subjects and their status
```

**Deliverables**: System for managing multiple interviews per incident

---

## Day 6: Synthesis Agent - Analysis & Contradiction Detection

### Objectives
1. Build agent that analyzes all interviews together
2. Identify contradictions between accounts
3. Find consensus points
4. Generate follow-up question suggestions
5. Create visual report output

### Pseudocode
```
# Synthesis Agent
class SynthesisAgent:
    def analyze_investigation(investigation):
        all_transcripts = investigation.interviews
        all_facts = investigation.all_facts
        
        analysis = {
            "timeline": self.build_timeline(all_facts),
            "contradictions": self.find_contradictions(all_facts),
            "consensus": self.find_consensus(all_facts),
            "suggested_followups": self.suggest_followups(all_facts)
        }
        
        return analysis
    
    def find_contradictions(all_facts):
        contradiction_prompt = f"""
        Interview facts from multiple subjects:
        {format_facts_by_subject(all_facts)}
        
        Identify contradictions where subjects give incompatible accounts.
        
        Return JSON array: [
            {{
                "topic": "who brought the cake",
                "accounts": {{
                    "Alex": "Sarah forgot it",
                    "Sarah": "It was in my car"
                }},
                "severity": "high|medium|low"
            }}
        ]
        """
        
        return call_llm(contradiction_prompt, json_mode=True)
    
    def find_consensus(all_facts):
        consensus_prompt = f"""
        Facts from all interviews: {all_facts}
        
        What do multiple subjects agree on?
        Return facts mentioned by 2+ people with similar framing.
        """
        
        return call_llm(consensus_prompt, json_mode=True)
    
    def build_timeline(all_facts):
        # Extract time-referenced events
        # Use LLM to order chronologically
        # Merge overlapping accounts
        timeline_prompt = f"""
        Extract time-referenced events from: {all_facts}
        Build chronological timeline.
        Note where accounts differ on timing.
        """
        
        return call_llm(timeline_prompt, json_mode=True)
    
    def suggest_followups(all_facts):
        # Based on contradictions and gaps
        followup_prompt = f"""
        Given these contradictions and gaps in the story:
        {self.contradictions}
        
        Suggest specific follow-up questions to resolve discrepancies.
        """
        
        return call_llm(followup_prompt)

# Report Generation
generate_report(investigation_id):
    investigation = load_investigation(investigation_id)
    analysis = SynthesisAgent().analyze_investigation(investigation)
    
    # Pretty print report
    print(f"""
    📊 Analysis Report: "{investigation.incident_name}"
    {'='*60}
    
    Timeline of Events:
    {format_timeline(analysis.timeline)}
    
    Contradictions Detected:
    {format_contradictions(analysis.contradictions)}
    
    Consensus Points:
    {format_consensus(analysis.consensus)}
    
    Suggested Follow-ups:
    {format_followups(analysis.suggested_followups)}
    """)

# CLI Command
drama analyze <investigation_id>
    -> runs synthesis
    -> displays report
    -> optionally saves to file
```

**Deliverables**: Comprehensive analysis comparing all interviews

---

## Day 7: Polish, UX, Testing & Documentation

### Objectives
1. Add personality and humor to agent responses
2. Create engaging ASCII art and formatting
3. Write comprehensive README with examples
4. Add error handling and input validation
5. Create demo mode with simulated responses
6. Record demo video/GIF

### Pseudocode
```
# Personality Layer
class PersonalityWrapper:
    def add_personality(agent_message):
        # Add occasional emojis
        # Use casual phrasing
        # Add investigator-style interjections
        
        examples = [
            "Interesting... 🤔",
            "Hold up, let me write that down...",
            "Okay okay, I'm hearing you.",
            "[scribbles in notebook]"
        ]

# Demo Mode
demo_mode(incident_name):
    # LLM plays all subjects with different personalities
    subjects = ["Alex", "Sarah", "Jordan"]
    
    for subject in subjects:
        persona_prompt = f"""
        You are {subject} being interviewed about: {incident_name}
        Personality: [generate random personality traits]
        
        Respond to questions as this character.
        Be slightly contradictory to other accounts.
        Include realistic speech patterns and deflections.
        """
        
        # Run automated interview with LLM playing both sides
        conduct_simulated_interview(subject, persona_prompt)
    
    # Then run analysis
    generate_report()

# Error Handling
add_robust_error_handling():
    - API rate limits -> retry with exponential backoff
    - Invalid session IDs -> helpful error message
    - Network errors -> save state before crashing
    - Malformed LLM responses -> parse gracefully or re-query
    - File permission issues -> clear error messages

# README Structure
write_readme():
    ## Drama Detective 🔍
    
    ### What is this?
    [Explain the concept + technical inspiration from Fractional AI]
    
    ### Quick Start
    [Installation, API key setup, first command]
    
    ### Example Usage
    [Full example with real output]
    
    ### Architecture
    [Diagram showing multi-agent system]
    
    ### Technical Details
    [Multi-agent architecture, LLM usage, state management]
    
    ### Why I Built This
    [Connect to Fractional AI job application]

# ASCII Art
create_cli_branding():
    ```
    ╔═══════════════════════════════════╗
    ║   🔍 DRAMA DETECTIVE v1.0 🔍    ║
    ║   Truth-seeking AI interviewer   ║
    ╚═══════════════════════════════════╝
    ```

# Testing
create_test_suite():
    - Test drift detection with off-topic responses
    - Test contradiction detection with known conflicts
    - Test session pause/resume
    - Test multi-subject investigation flow
    - Test edge cases (empty responses, very long answers)
```

**Deliverables**: Polished, documented, demo-ready project

---

## Success Criteria

By end of Day 7, you should have:

✅ Working CLI with multiple commands
✅ Multi-agent architecture (interviewer, drift detector, next-question, synthesis)
✅ Multiple interview subjects per investigation
✅ Analysis report with contradictions and consensus
✅ Session state management (pause/resume)
✅ Clean, documented code
✅ Engaging demo with personality
✅ Strong README connecting to Fractional AI work

---

## Stretch Goals (If Time Permits)

- **Conversation branching**: Let user choose between suggested questions
- **Export formats**: Generate reports as PDF or HTML
- **Web scraping integration**: Pull "evidence" from group chat screenshots
- **Voice mode**: Use actual audio I/O instead of text
- **Evaluation framework**: Score interview quality

---

## Demo Talking Points for Interview

*"I built Drama Detective after reading your Superintelligent case study. The architecture mirrors what you built—adaptive questioning, drift detection, multi-source synthesis—but applied to investigating friend group drama instead of enterprise agent opportunities.*

*The multi-agent system includes an interviewer agent that adjusts questions based on responses, a drift detector that keeps conversations on track, a next-question selector that determines optimal question sequencing, and a synthesis agent that analyzes all interviews to find contradictions and consensus.*

*While this is a humor project, the underlying technical challenges are real: conversational state management, context-aware question generation, and extracting structured insights from unstructured conversations. These are the same problems you solve for your clients, just with different stakes."*

---

**Ready to build?** Take this plan to Claude Code and start with Day 1!