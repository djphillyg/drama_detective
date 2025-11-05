from typing import Optional

from src.api_client import ClaudeClient
from src.models import Fact, Goal, Message
from src.prompts import QUESTION_WITH_ANSWERS_SYSTEM, build_question_with_answers_prompt
from src.schemas import QUESTION_WITH_ANSWERS_SCHEMA


class QuestionGeneratorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    # v1: the question will come with answers, could implement with vapi or somethign
    def generate_question_with_answers(
        self,
        goals: list[Goal],
        facts: list[Fact],
        messages: list[Message],
        drift_redirect: str = "",
        session_id: Optional[str] = None,
        interviewee_name: str = "",
        interviewee_role: str = "",
    ) -> dict:
        # Calculate average confidence across goals
        avg_confidence = sum(g.confidence for g in goals) / len(goals) if goals else 0

        # Convert models to dicts for prompt
        goals_dicts = [
            {
                "description": g.description,
                "confidence": g.confidence,
                "status": g.status.value,
            }
            for g in goals
        ]
        facts_dicts = [
            {"claim": f.claim, "topic": f.topic, "timestamp": f.timestamp}
            for f in facts
        ]
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]

        # Build user prompt (include drift_redirect if present)
        user_prompt = build_question_with_answers_prompt(
            goals_dicts, facts_dicts, messages_dicts, drift_redirect, interviewee_name, interviewee_role
        )

        # Call Claude API with tool schema enforcement
        question_data = self.client.call_with_tool(
            QUESTION_WITH_ANSWERS_SYSTEM,
            user_prompt,
            QUESTION_WITH_ANSWERS_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Schema guarantees valid structure - no extraction/assertion needed
        if avg_confidence > 90:
            question_data["target_goal"] = "wrap_up"

        return question_data
