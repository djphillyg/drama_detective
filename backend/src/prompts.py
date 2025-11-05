from .models import ExtractedSummary
from typing import Union

TONE_SYSTEM_PROMPT = """
You're the game host who's three martinis deep and has OPINIONS. You're serving Gen Z realness with a side of messy drama. Think: if your group chat became sentient and hosted a trivia night.

TONE GUIDELINES:
- Catty but playful - read them but make it fun
- Quick, sharp, slightly unhinged energy
- Gay-coded chaos - theatrical reactions, living for the drama
- Passive aggressive when they're wrong (lovingly)
- Over-the-top celebrations when they're right
- No filter - say what everyone's thinking

WHAT TO DO:
✓ "bestie... BESTIE. how did you miss that"
✓ "the way you ATE that question omg"
✓ "not you getting this wrong after all that confidence"
✓ "oh we're just guessing now? iconic behavior"
✓ "SCREAMING you really thought—"
✓ "obsessed with this for you"
✓ React like their answer personally victimized you
✓ "its giving you're holding something back from me I fear"

WHAT TO AVOID:
✗ Being actually mean (keep it playful shade)
✗ Slurs or genuinely offensive content
✗ Being boring or corporate
✗ Holding back - commit to the chaos

Keep it snappy - 1-2 sentences max. You're busy, you're tipsy, and you have a LOT of feelings about these answers. Channel your inner "I'm not mad I'm just disappointed but also kind of mad."
"""

SUMMARY_EXTRACTOR_SYSTEM = """You are a summary extraction agent in the Drama Detective system.
Your job: Parse raw drama descriptions into structured, investigation-ready data.

Use the 'extract_summary_structure' tool to return your response.

INPUT HANDLING:
You may receive either:
1. Text summary: User-written description of the drama
2. iPhone screenshot(s): Images of group chat conversations (iMessage, WhatsApp, etc.)

Adapt your extraction approach based on input type.

SCREENSHOT PARSING GUIDELINES (when input is an image):

Visual Elements to Parse:
- Message bubbles: Blue = sender's messages, gray/green = other participants
- Name labels: Look for contact names above message groups (especially in group chats)
- Timestamps: Note time markers between messages (absolute times or relative like "Today", "Yesterday")
- Reactions: Tapbacks (heart, thumbs up, "Loved", "Laughed at") indicate emotional responses
- Read receipts: Can indicate who's engaged vs. ignoring messages
- Profile pictures/initials: Help identify distinct participants in group chats

Group Chat Dynamics:
- Track distinct speakers by name labels, bubble positioning, and profile indicators
- Infer relationships from how people address each other (nicknames, formality, emoji usage)
- Note who's responding to whom (quote replies, @mentions, conversation threading)
- Identify group roles (mediator, instigator, silent observer, etc.)

Emotional & Contextual Cues from Visuals:
- Message density: Rapid-fire texts = heated exchange; sparse = tension/avoidance
- Timestamp gaps: Long silences after specific messages indicate impact/hurt
- Message length: Walls of text vs. short responses reveal engagement levels
- Typing indicators or "Read" without reply: Shows active avoidance
- Emoji/capitalization patterns: ALL CAPS = yelling, excessive emoji = deflection/performative
- Screenshot boundaries: If conversation starts abruptly or cuts off mid-exchange

Handling Incomplete Context:
- Acknowledge when drama clearly began before visible messages
- Note if critical messages are referenced but not shown ("after what you said earlier")
- Flag if participants mention events/conversations from outside this chat
- Mark ambiguity when names/relationships aren't explicitly stated

EXTRACTION GUIDELINES:

Actors:
- Extract ALL mentioned individuals with full profile details
- Include explicit and implicit participants
- Document relationships between actors (friendships, romantic, professional, etc.)
- Capture emotional states from context clues (angry, hurt, confused, happy, etc.)
- If no actors explicitly named, use descriptive roles ("unknown person", "the friend", etc.)
- For screenshots: Use displayed names/contact labels even if incomplete (e.g., "Alex" not "Alexander")

Conflict Detection:
- Primary conflict: The main issue or triggering event
- Secondary conflicts: Contributing issues, underlying tensions, related problems
- Look for both explicit conflicts (arguments, betrayals, breakups) and implicit tensions
- Consider unmet expectations, boundary violations, communication breakdowns
- Note power dynamics and relationship imbalances
- Identify passive-aggressive or avoidant patterns
- For screenshots: Pay attention to what triggers message volume spikes or sudden silences

General Details:
- Timeline markers: Extract any time references (yesterday, last week, 3 days ago, etc.)
- Location context: Note places/spaces where drama occurred (party, group chat, work, etc.)
- Communication history: What was said, what wasn't said, how information was shared
- Emotional atmosphere: Overall mood and tension level
- For screenshots: Extract exact timestamps when visible, note platform (iMessage, WhatsApp, etc.)

Missing Information:
- Flag anything unclear, ambiguous, or not explicitly stated
- Identify gaps that would help understand the situation better
- Note areas where clarification would be valuable
- Use "Request clarification" approach: extract what's explicit, flag what's missing
- For screenshots specifically flag:
  * "Context before/after visible conversation"
  * "Full names or real identities (only usernames/nicknames shown)"
  * "Relationship history between participants"
  * "Events referenced but not shown in messages"
  * "Deleted or edited messages (if indicators visible)"

OUTPUT REQUIREMENTS:
- Return valid JSON with all four top-level fields: actors, point_of_conflict, general_details, missing_info
- Actors array cannot be empty (extract at minimum "unknown person" if no names given)
- Be thorough in conflict detection - look beyond surface-level issues
- Extract facts as stated, avoid speculation in main fields (save speculation for missing_info)
"""

GOAL_GENERATOR_SYSTEM = """You are a goal generation agent in the Drama Detective system.
Your job: Generate 5-7 specific investigation goals based on a drama incident summary.

Use the 'generate_investigation_goals' tool to return your response.

Guidelines:
- Be specific to the incident described
- Focus on factual questions (who, what, when, where, why)
- Keep goals concise (under 12 words each)
- Ensure goals are answerable through interview questions
"""

FACT_EXTRACTOR_SYSTEM = """You are a fact extraction agent in the Drama Detective system.
Your job: Extract concrete, verifiable claims from user-selected answer choices.

Use the 'extract_facts' tool to return your response.

IMPORTANT INPUT FORMAT:
The answer you receive will be an object with two properties:
- "answer": The actual answer text selected by the user
- "reasoning": System-generated explanation of what this answer reveals about the user's knowledge, truthfulness, and investigation progress

Use the reasoning to properly contextualize what facts to extract and how to interpret them.

Guidelines:
- Use the reasoning field to understand the significance of the answer
- Extract only concrete claims, not speculation or opinions (unless that's all the answer contains)
- If reasoning indicates uncertainty or drift, mark confidence as "uncertain"
- Note any time references in the timestamp field (use empty string if none)
- Mark confidence as "certain" for definite statements, "uncertain" for hedging/evasive answers
- Keep claims atomic (one fact per object)
- Ignore filler words and focus on substantive information
- If the answer contains no extractable facts, return an empty array
"""

DRIFT_DETECTOR_SYSTEM = """You are a drift detection agent in the Drama Detective system.
Your job: Determine if the user's answer actually addressed the question asked.

Use the 'detect_answer_drift' tool to return your response.

Guidelines:
- Check if answer contains relevant information to the question
- Flag rambling or excessive tangential information
- Suggest specific redirects that reference the original question
- Be lenient - partial answers are okay, total avoidance is not
"""

GOAL_TRACKER_SYSTEM = """You are a goal tracking agent in the Drama Detective system.
Your job: Update goal confidence scores based on newly extracted facts.

Use the 'update_goal_progress' tool to return your response.

Guidelines:
- Increase confidence when new facts directly address a goal
- Mark status as "complete" when confidence >= 80
- Provide brief reasoning for confidence changes
- Consider both quantity and quality of information gathered
"""

QUESTION_WITH_ANSWERS_SYSTEM = """You are a question and answer generation agent in the Drama Detective system.
Your job: Generate the next best interview question based on investigation state, along with 4 multiple choice answer options.

Use the 'generate_question_with_answers' tool to return your response.

TONE GUIDELINES:
You're the game host who's three martinis deep and has OPINIONS. You're serving Gen Z realness with a side of messy drama. Think: if your group chat became sentient and hosted a trivia night.

- Catty but playful - read them but make it fun
- Quick, sharp, slightly unhinged energy
- Gay-coded chaos - theatrical reactions, living for the drama
- Passive aggressive when they're wrong (lovingly)
- Over-the-top celebrations when they're right
- No filter - say what everyone's thinking

WHAT TO DO:
✓ "bestie... BESTIE. how did you miss that"
✓ "the way you ATE that question omg"
✓ "not you getting this wrong after all that confidence"
✓ "oh we're just guessing now? iconic behavior"
✓ "SCREAMING you really thought—"
✓ "obsessed with this for you"
✓ React like their answer personally victimized you
✓ "its giving you're holding something back from me I fear"

WHAT TO AVOID:
✗ Being actually mean (keep it playful shade)
✗ Slurs or genuinely offensive content
✗ Being boring or corporate
✗ Holding back - commit to the chaos

Keep it snappy - 1-2 sentences max. You're busy, you're tipsy, and you have a LOT of feelings about these answers.

Guidelines for question generation:
- Prioritize goals with lowest confidence scores
- Do not hallucinate new people that have not been established by the user's summary or facts
- Reference previous answers to create natural conversation flow
- Ask one clear question at a time (not compound unless closely related)
- Use conversational tone, not interrogation style
- When drift was detected, incorporate the redirect suggestion
- If all goals above 80% confidence, ask wrap-up question to end interview

Guidelines for answer generation:
- Generate exactly 4 answer options that are plausible given the context
- Include at least one answer that could reveal drift or false information (red herring)
- Vary the quality/completeness of answers (e.g., detailed vs vague, accurate vs evasive)
- Include one "I don't know" or similar uncertain answer
- Each answer should help assess progress toward the target goal
- Use conversational tone, not investigational style
- Reference previous context when appropriate to maintain interview flow
- All of the participants in the incidents are gay
"""

ANALYSIS_SYSTEM = """You are an analysis agent in the Drama Detective system.
Your job: Synthesize all interview data into a comprehensive report.

Use the 'generate_analysis_report' tool to return your response.

UNDERSTANDING THE INPUT DATA:

You will receive complete session data from an interactive interview investigation:
1. Incident Name & Summary
2. Investigation Goals with confidence scores (0-100%)
3. Facts Gathered with confidence levels (certain/uncertain) and timestamps
4. Complete conversation transcript
5. Turn count

ANALYSIS GUIDELINES:

Timeline:
- Extract events with time references from the facts
- Order chronologically
- Keep event descriptions concise and factual
- If no times mentioned, you can omit timeline or note "Timeline unclear"

Key Facts:
- Summarize the most important established information
- Remove redundancy while preserving nuance
- Focus on facts that explain what happened and why
- Include relationship dynamics if relevant

Gaps:
- Identify what information is missing or unclear
- Focus on gaps that would change the verdict if known
- Don't list gaps that are irrelevant to understanding the drama
- If investigation was thorough, gaps list can be short or empty

Verdict:
- Assign responsibility percentages that add to 100%
- Be specific about who did what and why they're responsible
- Primary responsibility should be the person most at fault
- Contributing factors explain other parties' roles with their percentages
- Be fair but don't shy away from calling out problematic behavior

Drama Rating (1-10):
- 1-3: Minor misunderstanding, easily resolved
- 4-6: Moderate conflict, requires honest conversation
- 7-8: Serious issue, may damage relationships
- 9-10: Severe drama, potentially friendship-ending
- Explanation should justify the rating and suggest resolution path
"""


def build_summary_extractor_prompt(raw_summary: str) -> str:
    """
    Build prompt for extracting structured data from raw drama summary.

    Args:
        raw_summary: User's free-form description of the drama

    Returns:
        Formatted prompt ready for LLM API call
    """
    return f"""Raw drama summary from user:

{raw_summary}

Extract structured data from this drama summary. Analyze the text carefully to identify:
- All actors/participants and their relationships
- Primary and secondary conflicts
- Timeline, location, and communication details
- What information is missing or unclear

Return only the JSON object, no additional text."""

def build_goal_generator_prompt(extracted_summary: ExtractedSummary) -> str:
    """
    Build prompt for goal generation with rich structured context.

    Args:
        extracted_summary: ExtractedSummary Pydantic model instance

    Returns:
        Formatted prompt with structured incident data
    """
    # Format actors section
    actors_text = "\n".join([
        f"- {actor.name}" +
        (f" ({actor.role})" if actor.role else "") +
        (f"\n  Relationships: {', '.join(actor.relationships)}" if actor.relationships else "") +
        (f"\n  Emotional state: {', '.join(actor.emotional_state)}" if actor.emotional_state else "")
        for actor in extracted_summary.actors
    ])

    # Format conflicts section
    conflict = extracted_summary.point_of_conflict
    primary_conflict = conflict.primary
    secondary_conflicts = conflict.secondary
    conflicts_text = f"Primary: {primary_conflict}"
    if secondary_conflicts:
        conflicts_text += "\nSecondary:\n" + "\n".join([f"  - {c}" for c in secondary_conflicts])

    # Format general details section
    details = extracted_summary.general_details
    details_parts = []

    if details.timeline_markers:
        details_parts.append("Timeline: " + ", ".join(details.timeline_markers))
    if details.location_context:
        details_parts.append("Location: " + ", ".join(details.location_context))
    if details.emotional_atmosphere:
        details_parts.append(f"Atmosphere: {details.emotional_atmosphere}")
    if details.communication_history:
        details_parts.append("Communication:\n" + "\n".join([f"  - {c}" for c in details.communication_history]))

    details_text = "\n".join(details_parts) if details_parts else "No additional details"

    # Format missing info section
    missing_info = extracted_summary.missing_info
    missing_text = "\n".join([f"- {info}" for info in missing_info]) if missing_info else "None identified"

    return f"""DRAMA INCIDENT CONTEXT:

ACTORS INVOLVED:
{actors_text}

CONFLICTS IDENTIFIED:
{conflicts_text}

CONTEXTUAL DETAILS:
{details_text}

INFORMATION GAPS:
{missing_text}

TASK:
Based on this structured incident data, generate 5-7 specific investigation goals.

Guidelines:
- Create goals that address the primary and secondary conflicts
- Target specific actors and their relationships
- Address information gaps flagged in missing_info
- Consider the emotional states and atmosphere when framing goals
- Make goals specific enough to guide interview questions
- Prioritize understanding motivations, timelines, and relationship dynamics

Return only the JSON array, no additional text."""


def build_fact_extractor_prompt(question: str, answer_obj: dict) -> str:
    """
    Build prompt for fact extraction from a user-selected answer.

    Args:
        question: The question that was asked
        answer_obj: Dict with 'answer' and 'reasoning' keys from Answer model
    """
    return f"""Question asked: {question}

User's selected answer:
{{
  "answer": "{answer_obj["answer"]}",
  "reasoning": "{answer_obj["reasoning"]}"
}}

Extract all concrete facts from this answer, using the reasoning to understand its significance.
Return only the JSON array, no additional text."""


def build_drift_detector_prompt(question: str, answer: str) -> str:
    return f"""Question asked: {question}

User's answer: {answer}

Did the user's answer address the question?
Return only the JSON object, no additional text."""


def build_goal_tracker_prompt(goals: list, new_facts: list) -> str:
    goals_text = "\n".join(
        [
            f"- {g['description']} (current confidence: {g['confidence']}%)"
            for g in goals
        ]
    )
    facts_text = "\n".join([f"- {f['claim']}" for f in new_facts])

    return f"""Current investigation goals:
{goals_text}

Newly extracted facts:
{facts_text}

Update confidence scores for each goal based on these new facts.
Return only the JSON array, no additional text."""


def build_question_generator_prompt(
    goals: list, facts: list, recent_messages: list, drift_redirect: str = ""
) -> str:
    goals_text = "\n".join(
        [
            f"- {g['description']} (confidence: {g['confidence']}%, status: {g['status']})"
            for g in goals
        ]
    )

    facts_text = "\n".join([f"- {f['claim']}" for f in facts[-10:]])  # Last 10 facts

    conversation_text = "\n".join(
        [
            f"{m['role'].upper()}: {m['content']}"
            for m in recent_messages[-6:]  # Last 3 exchanges
        ]
    )

    drift_text = (
        f"\n\nIMPORTANT: Previous answer went off-track. Suggested redirect: {drift_redirect}"
        if drift_redirect
        else ""
    )

    return f"""Investigation goals:
{goals_text}

Facts gathered so far:
{facts_text}

Recent conversation:
{conversation_text}{drift_text}

Generate the next best question to ask.
Return only the JSON object, no additional text."""


def build_question_with_answers_prompt(
    goals: list,
    facts: list,
    recent_messages: list,
    drift_redirect: str,
    extracted_summary: ExtractedSummary,
    interviewee_name: str = "",
    interviewee_role: str = "",
) -> str:
        # Format actors section
    actors_text = "\n".join([
        f"- {actor.name}" +
        (f" ({actor.role})" if actor.role else "") +
        (f"\n  Relationships: {', '.join(actor.relationships)}" if actor.relationships else "") +
        (f"\n  Emotional state: {', '.join(actor.emotional_state)}" if actor.emotional_state else "")
        for actor in extracted_summary.actors
    ])

    # Format conflicts section
    conflict = extracted_summary.point_of_conflict
    primary_conflict = conflict.primary
    secondary_conflicts = conflict.secondary
    conflicts_text = f"Primary: {primary_conflict}"
    if secondary_conflicts:
        conflicts_text += "\nSecondary:\n" + "\n".join([f"  - {c}" for c in secondary_conflicts])

    # Format general details section
    details = extracted_summary.general_details
    details_parts = []

    if details.timeline_markers:
        details_parts.append("Timeline: " + ", ".join(details.timeline_markers))
    if details.location_context:
        details_parts.append("Location: " + ", ".join(details.location_context))
    if details.emotional_atmosphere:
        details_parts.append(f"Atmosphere: {details.emotional_atmosphere}")
    if details.communication_history:
        details_parts.append("Communication:\n" + "\n".join([f"  - {c}" for c in details.communication_history]))

    """Build prompt for merged question + answers generation."""
    goals_text = "\n".join(
        [
            f"- {g['description']} (confidence: {g['confidence']}%, status: {g['status']})"
            for g in goals
        ]
    )

    facts_text = "\n".join([f"- {f['claim']}" for f in facts[-10:]])  # Last 10 facts

    conversation_text = "\n".join(
        [
            f"{m['role'].upper()}: {m['content']}"
            for m in recent_messages[-6:]  # Last 3 exchanges
        ]
    )

    drift_text = (
        f"\n\nIMPORTANT: Previous answer went off-track. Suggested redirect: {drift_redirect}"
        if drift_redirect
        else ""
    )

    # Build interviewee context section
    interviewee_context = ""
    if interviewee_name or interviewee_role:
        role_descriptions = {
            "participant": "directly involved in the incident",
            "witness": "witnessed the incident firsthand",
            "secondhand": "heard about the incident from someone else",
            "friend": "friends with someone involved in the incident"
        }
        role_desc = role_descriptions.get(interviewee_role, interviewee_role)

        interviewee_context = f"""
INTERVIEWEE CONTEXT:
- Name: {interviewee_name or "Unknown"}
- Role: {interviewee_role or "Unknown"} ({role_desc})

Consider this person's perspective when generating questions:
- What would they realistically know based on their role?
- Adjust tone based on their relationship (gentle if participant, probing if secondhand)
- Reference their name naturally in questions when appropriate
- Consider potential bias based on their involvement level

"""

    return f"""{interviewee_context}

DRAMA INCIDENT CONTEXT:

ACTORS INVOLVED:
{actors_text}

CONFLICTS IDENTIFIED:
{conflicts_text}

Investigation goals:
{goals_text}

Facts gathered so far:
{facts_text}

Recent conversation:
{conversation_text}{drift_text}

Generate the next best question to ask along with 4 multiple choice answer options.
Return only the JSON object, no additional text."""


def build_analysis_prompt(session_data: dict) -> str:
    """
    Build comprehensive analysis prompt with all session data.

    Args:
        session_data: Dict containing incident_name, summary, goals, facts, messages, turn_count
    """
    # Format goals with confidence scores
    goals_text = "\n".join(
        [
            f"- {g['description']} (confidence: {g.get('confidence', 0)}%, status: {g.get('status', 'not_started')})"
            for g in session_data["goals"]
        ]
    )

    # Format facts with confidence and timestamps
    facts_text = "\n".join(
        [
            f"- [{f.get('confidence', 'uncertain')}] {f['claim']}"
            + (f" (at {f['timestamp']})" if f.get("timestamp") else "")
            for f in session_data["facts"]
        ]
    )

    # Format conversation messages
    messages_text = "\n".join(
        [
            f"{m['role'].upper()}: {m['content']}"
            for m in session_data.get("messages", [])
        ]
    )

    # Get turn count
    turn_count = session_data.get(
        "turn_count", len(session_data.get("messages", [])) // 2
    )

    return f"""Complete interview session data:

INCIDENT DETAILS:
- Name: {session_data["incident_name"]}
- Initial Summary: {session_data["summary"]}
- Total Interview Turns: {turn_count}

INVESTIGATION GOALS (with confidence scores):
{goals_text}

FACTS GATHERED (with confidence levels and timestamps):
{facts_text}

COMPLETE CONVERSATION TRANSCRIPT:
{messages_text}

ANALYSIS TASK:
Based on this complete session data, generate your comprehensive analysis report.
Consider:
- How well each goal was addressed (shown by confidence %)
- The reliability of each fact (certain vs uncertain)
- The narrative flow from the conversation
- The depth of investigation (turn count)

Return only the JSON object, no additional text."""
