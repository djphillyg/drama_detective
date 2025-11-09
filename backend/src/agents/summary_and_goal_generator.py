from typing import Optional

from ..api_client import ClaudeClient
from ..models import ExtractedSummary, Goal, GoalStatus
from ..prompts import build_summary_and_goals_prompt, SUMMARY_AND_GOAL_GENERATION_SYSTEM
from ..schemas import SUMMARY_EXTRACTOR_SCHEMA, GOAL_GENERATOR_SCHEMA


class SummaryAndGoalGenerator:
    """
    Combined agent that extracts summary AND generates goals in a single API call.

    This reduces latency during initialization by combining two sequential operations,
    using Claude's multi-tool calling capability.
    """

    def __init__(self, client: ClaudeClient):
        self.client = client

    def extract_and_generate(
        self,
        raw_summary: str,
        image_data_list: list[dict] = None,
        session_id: Optional[str] = None
    ) -> tuple[ExtractedSummary, list[Goal]]:
        """
        Extract structured summary from text/images AND generate investigation goals in one API call.

        Args:
            raw_summary: User's raw drama description text
            image_data_list: Optional list of image dicts for vision processing
            session_id: Optional session ID for context isolation

        Returns:
            Tuple of (extracted_summary, goals)
        """
        # Build prompt
        user_prompt = build_summary_and_goals_prompt(raw_summary)

        # Determine if we need vision processing
        if image_data_list and len(image_data_list) > 0:
            # Build content array with images + text
            content = []
            for img in image_data_list:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img["media_type"],
                        "data": img["data"]
                    }
                })
            content.append({
                "type": "text",
                "text": user_prompt
            })

            # Call with images using custom implementation
            # Note: We need to add a multi-tool version of call_with_tool_and_images
            # For now, fall back to sequential calls if images are present
            # TODO: Implement call_with_multiple_tools_and_images
            raise NotImplementedError(
                "Multi-tool calling with images not yet implemented. "
                "Use separate summary_extractor and goal_generator for image-based summaries."
            )
        else:
            # Call with multiple tools (text only)
            tool_results = self.client.call_with_multiple_tools(
                SUMMARY_AND_GOAL_GENERATION_SYSTEM,
                user_prompt,
                [SUMMARY_EXTRACTOR_SCHEMA, GOAL_GENERATOR_SCHEMA],
                session_id=session_id,
                use_cache=True
            )

        # Extract summary from tool results
        summary_data = tool_results.get("extract_summary_structure", {})
        extracted_summary = ExtractedSummary(**summary_data)

        # Extract goals from tool results
        goals_data = tool_results.get("generate_investigation_goals", {})
        goal_strings = goals_data.get("goals", [])

        # Convert goal strings to Goal objects (start with 0 confidence)
        goals = [
            Goal(
                description=goal_str,
                confidence=0,
                status=GoalStatus.NOT_STARTED
            )
            for goal_str in goal_strings
        ]

        return extracted_summary, goals