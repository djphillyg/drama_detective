import os
import time
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
        # TODO: Call Claude API with retry logic
        # - Try up to max_retries times
        # - Use exponential backoff (2^attempt seconds)
        # - Return response.content[0].text
        # - Raise exception if all retries fail
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