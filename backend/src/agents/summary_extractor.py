"""Summary Extractor Agent for parsing raw drama descriptions into structured data."""

from typing import Optional

from ..api_client import ClaudeClient
from ..prompts import SUMMARY_EXTRACTOR_SYSTEM, build_summary_extractor_prompt
from ..schemas import SUMMARY_EXTRACTOR_SCHEMA
from ..models import ExtractedSummary


class SummaryExtractorAgent:
    """Agent that extracts structured data from raw drama summaries."""

    def __init__(self, client: ClaudeClient):
        """
        Initialize the SummaryExtractorAgent.

        Args:
            client: ClaudeClient instance for API calls
        """
        self.client = client

    def extract_summary(self, raw_summary: str, image_data_list: list[dict], session_id: Optional[str] = None) -> ExtractedSummary:
        """
        Extract structured data from raw drama summary.

        Args:
            raw_summary: User's free-form description of the drama
            session_id: Optional session ID for caching

        Returns:
            ExtractedSummary model with actors, point_of_conflict, general_details, missing_info
        """
        
            # Validate at least one input provided
        if not raw_summary and not image_data_list:
            raise ValueError("Must provide either raw_summary or image_data_list")
        user_prompt = build_summary_extractor_prompt(raw_summary)
        
        # Build user prompt
        if image_data_list:
            response = self.client.call_with_tool_and_images(
                SUMMARY_EXTRACTOR_SYSTEM,
                user_prompt,
                SUMMARY_EXTRACTOR_SCHEMA,
                image_data_list=image_data_list,
                session_id=session_id,
                use_cache=True
            )
        elif not image_data_list:
            response = self.client.call_with_tool(
                SUMMARY_EXTRACTOR_SYSTEM,
                user_prompt,
                SUMMARY_EXTRACTOR_SCHEMA,
                session_id=session_id,
                use_cache=True
            )

        # Schema guarantees response has all required fields
        # Convert dict response to ExtractedSummary Pydantic model
        return ExtractedSummary.model_validate(response)