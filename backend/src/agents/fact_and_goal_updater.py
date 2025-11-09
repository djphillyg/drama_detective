from typing import Optional

from ..api_client import ClaudeClient
from ..models import Answer, Fact, Goal, GoalStatus
from ..prompts import build_fact_and_goal_update_prompt, FACT_AND_GOAL_UPDATE_SYSTEM
from ..schemas import FACT_EXTRACTOR_SCHEMA, GOAL_TRACKER_SCHEMA


class FactAndGoalUpdater:
    """
    Combined agent that extracts facts AND updates goals in a single API call.

    This reduces latency by combining two sequential operations into one,
    using Claude's multi-tool calling capability.
    """

    def __init__(self, client: ClaudeClient):
        self.client = client

    def extract_and_update(
        self,
        question: str,
        answer_obj: Answer,
        goals: list[Goal],
        session_id: Optional[str] = None
    ) -> tuple[list[Fact], list[Goal]]:
        """
        Extract facts from answer AND update goal confidence in one API call.

        Args:
            question: The question that was asked
            answer_obj: The selected answer with reasoning
            goals: Current investigation goals
            session_id: Optional session ID for context isolation

        Returns:
            Tuple of (extracted_facts, updated_goals)
        """
        # Build combined prompt
        user_prompt = build_fact_and_goal_update_prompt(
            question,
            answer_obj.model_dump(),
            [
                {
                    "description": g.description,
                    "confidence": g.confidence,
                    "status": g.status.value,
                }
                for g in goals
            ]
        )

        # Call with multiple tools
        tool_results = self.client.call_with_multiple_tools(
            FACT_AND_GOAL_UPDATE_SYSTEM,
            user_prompt,
            [FACT_EXTRACTOR_SCHEMA, GOAL_TRACKER_SCHEMA],
            session_id=session_id,
            use_cache=True
        )

        # Extract facts from tool results
        facts_list = tool_results.get("extract_facts", {}).get("facts", [])
        extracted_facts = [Fact(**fact_dict) for fact_dict in facts_list]

        # Extract goal updates from tool results
        goal_updates = tool_results.get("update_goal_progress", {}).get("goal_updates", [])

        # Apply updates to goals
        update_map = {update["goal"]: update for update in goal_updates}
        updated_goals = []

        for goal in goals:
            if goal.description in update_map:
                update = update_map[goal.description]
                updated_goal = Goal(
                    description=goal.description,
                    confidence=update["confidence"],
                    status=GoalStatus(update["status"]),
                )
                updated_goals.append(updated_goal)
            else:
                # Keep goal unchanged if no update found
                updated_goals.append(goal)

        return extracted_facts, updated_goals