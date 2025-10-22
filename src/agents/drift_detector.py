import json
from src.api_client import ClaudeClient
from src.prompts import DRIFT_DETECTOR_SYSTEM, build_drift_detector_prompt


class DriftDetectorAgent:
    def __init__(self, client: ClaudeClient):
        self.client = client

    def check_drift(self, question: str, answer: str) -> dict:
        # Build user prompt
        user_prompt = build_drift_detector_prompt(question, answer)

        # Call Claude API
        response = self.client.call(DRIFT_DETECTOR_SYSTEM, user_prompt)

        # Parse JSON response
        drift_analysis = self.client.extract_json_from_response(response)

        # Return drift analysis dict
        return drift_analysis