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

    def extract_summary(self, raw_summary: str, session_id: Optional[str] = None) -> ExtractedSummary:
        """
        Extract structured data from raw drama summary.

        Args:
            raw_summary: User's free-form description of the drama
            session_id: Optional session ID for caching

        Returns:
            ExtractedSummary model with actors, point_of_conflict, general_details, missing_info
        """
        # Build user prompt
        user_prompt = build_summary_extractor_prompt(raw_summary)

        # Call Claude API with tool schema enforcement
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