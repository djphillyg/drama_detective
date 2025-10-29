from typing import Optional

from src.api_client import ClaudeClient
from src.models import Fact, Goal, GoalStatus
from src.prompts import GOAL_TRACKER_SYSTEM, build_goal_tracker_prompt


class GoalTrackerAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def update_goals(
        self, goals: list[Goal], new_facts: list[Fact], session_id: Optional[str] = None
    ) -> list[Goal]:
        # Return unchanged goals if no new facts
        if not new_facts:
            return goals

        # Convert goals and facts to dicts for prompt
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
            for f in new_facts
        ]

        # Build user prompt
        user_prompt = build_goal_tracker_prompt(goals_dicts, facts_dicts)

        # Call Claude API
        response = self.client.call(
            GOAL_TRACKER_SYSTEM, user_prompt, session_id=session_id
        )

        # Parse JSON response
        updates = self.client.extract_json_from_response(response)

        # Assert that we received a list (not a dict)
        assert isinstance(updates, list), (
            f"Expected list of goal updates, got {type(updates).__name__}"
        )

        # Create update map by goal description
        update_map = {update["goal"]: update for update in updates}

        # Apply updates to each goal
        updated_goals = []
        for goal in goals:
            if goal.description in update_map:
                update = update_map[goal.description]
                # Create updated goal with new confidence and status
                updated_goal = Goal(
                    description=goal.description,
                    confidence=update["confidence"],
                    status=GoalStatus(update["status"]),
                )
                updated_goals.append(updated_goal)
            else:
                # Keep goal unchanged if no update found
                updated_goals.append(goal)

        # Return updated goals
        return updated_goals
