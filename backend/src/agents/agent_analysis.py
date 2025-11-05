from typing import Optional

from ..api_client import ClaudeClient
from ..models import AnalysisReport
from ..prompts import ANALYSIS_SYSTEM, build_analysis_prompt
from ..schemas import ANALYSIS_SCHEMA


class AnalysisAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def generate_analysis(
        self, session_data: dict, session_id: Optional[str] = None
    ) -> AnalysisReport:
        """
        Generate comprehensive analysis report for a drama incident.

        Args:
            session_data: Dict with incident_name, summary, goals, facts, messages, turn_count
            session_id: Optional session ID for context isolation

        Returns:
            AnalysisReport model with timeline, key_facts, gaps, verdict
        """
        # Build user prompt from session data
        user_prompt = build_analysis_prompt(session_data)

        # Call Claude API with tool schema enforcement
        response = self.client.call_with_tool(
            ANALYSIS_SYSTEM,
            user_prompt,
            ANALYSIS_SCHEMA,
            session_id=session_id,
            use_cache=True
        )

        # Convert dict response to AnalysisReport Pydantic model
        return AnalysisReport.model_validate(response)
