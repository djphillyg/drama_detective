from src.api_client import ClaudeClient
from src.prompts import ANALYSIS_SYSTEM, build_analysis_prompt


class AnalysisAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def generate_analysis(self, session_data: dict) -> dict:
        # Build user prompt from session data
        user_prompt = build_analysis_prompt(session_data)

        # Call Claude API
        response = self.client.call(ANALYSIS_SYSTEM, user_prompt)

        # Parse JSON response
        analysis = self.client.extract_json_from_response(response)

        # Assert that we received a dict (not a list)
        assert isinstance(analysis, dict), f"Expected dict for analysis, got {type(analysis).__name__}"

        # Return analysis dict
        return analysis