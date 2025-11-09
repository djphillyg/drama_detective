from typing import Optional

from ..api_client import ClaudeClient
from ..models import Fact, Goal, Message, ExtractedSummary, QuestionWithAnswers
from ..prompts import QUESTION_WITH_ANSWERS_SYSTEM, build_question_with_answers_prompt
from ..schemas import QUESTION_WITH_ANSWERS_SCHEMA


class QuestionGeneratorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    # v1: the question will come with answers, could implement with vapi or somethign
    def generate_question_with_answers(
        self,
        goals: list[Goal],
        facts: list[Fact],
        messages: list[Message],
        extracted_summary: ExtractedSummary,
        drift_redirect: str = "",
        session_id: Optional[str] = None,
        interviewee_name: str = "",
        interviewee_role: str = "",
        confidence_threshold: int = 90,
    ) -> QuestionWithAnswers:
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
            goals_dicts, facts_dicts, messages_dicts, drift_redirect, extracted_summary, interviewee_name, interviewee_role
        )

        # Call Claude API with tool schema enforcement
        response = self.client.call_with_tool(
            QUESTION_WITH_ANSWERS_SYSTEM,
            user_prompt,
            QUESTION_WITH_ANSWERS_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Override target_goal if investigation reaches user-specified confidence threshold
        if avg_confidence > confidence_threshold:
            response["target_goal"] = "wrap_up"

        # Convert dict response to QuestionWithAnswers Pydantic model
        return QuestionWithAnswers.model_validate(response)
