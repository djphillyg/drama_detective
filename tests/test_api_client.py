import pytest
from unittest.mock import Mock, patch
from drama_detective.api_client import ClaudeClient


class TestClaudeClient:
    """Test suite for ClaudeClient initialization and configuration"""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'mock-api-key-12345'})
    @patch('drama_detective.api_client.Anthropic')
    def test_client_initialization_with_defaults(self, mock_anthropic):
        """Test that ClaudeClient initializes with default parameters"""
        # Create ClaudeClient with defaults
        client = ClaudeClient()

        # Assert default values are set correctly
        assert client.model == "claude-3-7-sonnet-latest", "Default model should be claude-3-7-sonnet-latest"
        assert client.temperature == 0.3, "Default temperature should be 0.3"
        assert client.max_tokens == 4096, "Default max_tokens should be 4096"

        # Assert Anthropic client was initialized
        mock_anthropic.assert_called_once()
        assert client.client is not None, "Anthropic client should be initialized"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'mock-api-key-12345'})
    @patch('drama_detective.api_client.Anthropic')
    def test_client_initialization_with_custom_parameters(self, mock_anthropic):
        """Test that ClaudeClient accepts and stores custom parameters"""
        custom_model = "claude-3-opus-20240229"
        custom_temp = 0.7
        custom_tokens = 8192

        # Create ClaudeClient with custom parameters
        client = ClaudeClient(
            model=custom_model,
            temperature=custom_temp,
            max_tokens=custom_tokens
        )

        # Assert custom values are set correctly
        assert client.model == custom_model, f"Model should be {custom_model}"
        assert client.temperature == custom_temp, f"Temperature should be {custom_temp}"
        assert client.max_tokens == custom_tokens, f"Max tokens should be {custom_tokens}"

        # Assert Anthropic client was initialized
        mock_anthropic.assert_called_once()
        assert client.client is not None, "Anthropic client should be initialized"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key-abc123'})
    @patch('drama_detective.api_client.Anthropic')
    def test_client_uses_environment_api_key(self, mock_anthropic):
        """Test that ClaudeClient uses API key from environment variable"""
        # Create client
        client = ClaudeClient()

        # Verify Anthropic was called (it will read ANTHROPIC_API_KEY internally)
        mock_anthropic.assert_called_once()

        # Verify client was created
        assert client.client is not None, "Client should be initialized with environment API key"