from typing import Optional

from src.api_client import ClaudeClient
from src.prompts import ANALYSIS_SYSTEM, build_analysis_prompt
from src.schemas import ANALYSIS_SCHEMA


class AnalysisAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def generate_analysis(
        self, session_data: dict, session_id: Optional[str] = None
    ) -> dict:
        # Build user prompt from session data
        user_prompt = build_analysis_prompt(session_data)

        # Call Claude API with tool schema enforcement
        analysis = self.client.call_with_tool(
            ANALYSIS_SYSTEM,
            user_prompt,
            ANALYSIS_SCHEMA,
            session_id=session_id
        )

        # Schema guarantees valid dict structure
        return analysis
