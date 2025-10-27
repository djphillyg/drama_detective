from src.api_client import ClaudeClient
from src.prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def check_drift(
        self, question: str, answer: str, session_id: str | None = None
    ) -> dict:
        # Build user prompt
        user_prompt = build_drift_detector_prompt(question, answer)

        # Call Claude API
        response = self.client.call(
            DRIFT_DETECTOR_SYSTEM, user_prompt, session_id=session_id
        )

        # Parse JSON response
        drift_analysis = self.client.extract_json_from_response(response)

        # Assert that we received a dict (not a list)
        assert isinstance(drift_analysis, dict), (
            f"Expected dict for drift analysis, got {type(drift_analysis).__name__}"
        )

        # Return drift analysis dict
        return drift_analysis
