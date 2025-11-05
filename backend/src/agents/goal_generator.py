from typing import Optional

from ..api_client import ClaudeClient
from ..models import Goal, GoalStatus, ExtractedSummary
from ..prompts import GOAL_GENERATOR_SYSTEM, build_goal_generator_prompt
from ..schemas import GOAL_GENERATOR_SCHEMA


class GoalGeneratorAgent:
    def __init__(self, client: ClaudeClient):
        # TODO: Store client (or create new one if None)
        self.client = client
        pass

    def generate_goals(self, summary: ExtractedSummary, session_id: Optional[str] = None) -> list[Goal]:
        user_goal_prompt: str = build_goal_generator_prompt(summary)

        # Call Claude API with tool schema enforcement
        response = self.client.call_with_tool(
            GOAL_GENERATOR_SYSTEM,
            user_goal_prompt,
            GOAL_GENERATOR_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Schema guarantees response["goals"] is a list of strings
        goals_list = response["goals"]

        # Convert goal descriptions to Goal objects
        list_goals: list[Goal] = [
            Goal(description=goal_str, status=GoalStatus.NOT_STARTED)
            for goal_str in goals_list
        ]
        return list_goals
