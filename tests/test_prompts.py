"""Tests for prompt building functions."""

import pytest
from src.prompts import (
    build_summary_extractor_prompt,
    SUMMARY_EXTRACTOR_SYSTEM,
)


class TestBuildSummaryExtractorPrompt:
    """Test suite for build_summary_extractor_prompt function"""

    def test_function_exists(self):
        """Test that build_summary_extractor_prompt function exists"""
        assert callable(build_summary_extractor_prompt), (
            "build_summary_extractor_prompt should be a callable function"
        )

    def test_returns_string(self):
        """Test that function returns a string"""
        raw_summary = "John and Jane had a fight about the party"
        result = build_summary_extractor_prompt(raw_summary)
        assert isinstance(result, str), "Function should return a string"

    def test_includes_raw_summary(self):
        """Test that returned prompt includes the raw summary"""
        raw_summary = "John and Jane had a fight about the party"
        result = build_summary_extractor_prompt(raw_summary)
        assert raw_summary in result, "Prompt should include the raw summary text"

    def test_includes_json_instruction(self):
        """Test that prompt instructs to return JSON"""
        raw_summary = "Test drama"
        result = build_summary_extractor_prompt(raw_summary)
        assert "JSON" in result or "json" in result, (
            "Prompt should instruct to return JSON format"
        )

    def test_handles_empty_string(self):
        """Test that function handles empty string input"""
        result = build_summary_extractor_prompt("")
        assert isinstance(result, str), "Should return string even with empty input"
        assert len(result) > 0, "Should return non-empty prompt even with empty input"

    def test_handles_multiline_summary(self):
        """Test that function handles multiline summaries"""
        raw_summary = """Line 1 of drama
Line 2 of drama
Line 3 of drama"""
        result = build_summary_extractor_prompt(raw_summary)
        assert raw_summary in result, "Should preserve multiline summaries"

    def test_different_summaries_produce_different_prompts(self):
        """Test that different summaries produce different prompts"""
        summary1 = "Drama about John and Jane"
        summary2 = "Drama about Bob and Alice"

        result1 = build_summary_extractor_prompt(summary1)
        result2 = build_summary_extractor_prompt(summary2)

        assert result1 != result2, "Different summaries should produce different prompts"
        assert summary1 in result1, "First prompt should contain first summary"
        assert summary2 in result2, "Second prompt should contain second summary"


class TestSummaryExtractorSystem:
    """Test suite for SUMMARY_EXTRACTOR_SYSTEM constant"""

    def test_constant_exists(self):
        """Test that SUMMARY_EXTRACTOR_SYSTEM constant exists"""
        assert SUMMARY_EXTRACTOR_SYSTEM is not None, (
            "SUMMARY_EXTRACTOR_SYSTEM should exist"
        )

    def test_is_string(self):
        """Test that SUMMARY_EXTRACTOR_SYSTEM is a string"""
        assert isinstance(SUMMARY_EXTRACTOR_SYSTEM, str), (
            "SUMMARY_EXTRACTOR_SYSTEM should be a string"
        )

    def test_is_not_empty(self):
        """Test that SUMMARY_EXTRACTOR_SYSTEM is not empty"""
        assert len(SUMMARY_EXTRACTOR_SYSTEM.strip()) > 0, (
            "SUMMARY_EXTRACTOR_SYSTEM should not be empty"
        )

    def test_mentions_actors(self):
        """Test that system prompt mentions actors"""
        assert "actor" in SUMMARY_EXTRACTOR_SYSTEM.lower(), (
            "System prompt should mention actors"
        )

    def test_mentions_conflicts(self):
        """Test that system prompt mentions conflicts"""
        assert "conflict" in SUMMARY_EXTRACTOR_SYSTEM.lower(), (
            "System prompt should mention conflicts"
        )

    def test_mentions_extraction(self):
        """Test that system prompt mentions extraction"""
        assert "extract" in SUMMARY_EXTRACTOR_SYSTEM.lower(), (
            "System prompt should mention extraction"
        )

    def test_instructs_json_response(self):
        """Test that system prompt instructs JSON response"""
        prompt_lower = SUMMARY_EXTRACTOR_SYSTEM.lower()
        assert "json" in prompt_lower or "tool" in prompt_lower, (
            "System prompt should instruct JSON/tool response"
        )

    def test_mentions_drama_detective_system(self):
        """Test that system prompt mentions Drama Detective system"""
        assert "Drama Detective" in SUMMARY_EXTRACTOR_SYSTEM, (
            "System prompt should mention Drama Detective system"
        )