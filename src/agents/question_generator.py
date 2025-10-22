import json
from src.api_client import ClaudeClient
from src.prompts import QUESTION_WITH_ANSWERS_SYSTEM, build_question_with_answers_prompt
from src.models import Goal, Fact, Message


class QuestionGeneratorAgent:
    def __init__(self, client: ClaudeClient = None):
        self.client = client

    # v1: the question will come with answers, could implement with vapi or somethign
    def generate_question_with_answers(
        self,
        goals: list[Goal],
        facts: list[Fact],
        messages: list[Message],
        drift_redirect: str = ""
    ) -> dict:
        # Calculate average confidence across goals
        avg_confidence = sum(g.confidence for g in goals) / len(goals) if goals else 0

        # Convert models to dicts for prompt
        goals_dicts = [{"description": g.description, "confidence": g.confidence, "status": g.status.value} for g in goals]
        facts_dicts = [{"claim": f.claim, "topic": f.topic, "timestamp": f.timestamp} for f in facts]
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]

        # Build user prompt (include drift_redirect if present)
        user_prompt = build_question_with_answers_prompt(
            goals_dicts,
            facts_dicts,
            messages_dicts,
            drift_redirect
        )

        # Call Claude API
        response = self.client.call(QUESTION_WITH_ANSWERS_SYSTEM, user_prompt)

        # Parse JSON response
        question_data = self.client.extract_json_from_response(response)

        # Return question and answers in the parsed format it came in
        return question_data