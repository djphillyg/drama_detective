import json
from src.api_client import ClaudeClient
from src.prompts import GOAL_GENERATOR_SYSTEM, build_goal_generator_prompt
from src.models import Goal, GoalStatus


class GoalGeneratorAgent:
    def __init__(self, client: ClaudeClient):
        # TODO: Store client (or create new one if None)
        self.client = client
        pass

    def generate_goals(self, summary: str) -> list[Goal]:
        # TODO: Build user prompt from summary
        # Call Claude API with system + user prompt
        # Parse JSON response (handle cases where response has extra text)
        # Convert goal descriptions to Goal objects
        # Return list of Goal objects
        user_goal_prompt: str = build_goal_generator_prompt(summary)
        # call claude
        response = self.client.call(
            GOAL_GENERATOR_SYSTEM,
            user_goal_prompt
        )
        # clean the response
        cleaned_json: dict = self.client.extract_json_from_response(response)
        # extract out the descriptions to return a list of goals in the format
        list_goals: list[Goal] = [Goal(description=s, status=GoalStatus.NOT_STARTED) for s in cleaned_json]
        return list_goals