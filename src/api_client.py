import os
import time
import re
import json
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    def __init__(
        self,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Anthropic()
        pass

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model = self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt # exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
            
    def extract_json_from_response(self, response_text: str) -> dict:
        
        # Try different patterns in order of preference
        patterns = [
            r'```json\s*(.*?)\s*```',  # Markdown code block
            r'```\s*(.*?)\s*```',      # Generic code block
            r'\{.*\}',                 # Just the JSON object
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid JSON found in response")