"""Tests for JSON schemas used in tool-based LLM agent responses."""

import pytest
from src.schemas import SUMMARY_EXTRACTOR_SCHEMA


class TestSummaryExtractorSchema:
    """Test suite for SUMMARY_EXTRACTOR_SCHEMA validation"""

    def test_schema_exists(self):
        """Test that SUMMARY_EXTRACTOR_SCHEMA constant exists"""
        assert SUMMARY_EXTRACTOR_SCHEMA is not None, "SUMMARY_EXTRACTOR_SCHEMA should exist"

    def test_schema_has_required_fields(self):
        """Test that schema has name, description, and input_schema fields"""
        assert "name" in SUMMARY_EXTRACTOR_SCHEMA, "Schema should have 'name' field"
        assert "description" in SUMMARY_EXTRACTOR_SCHEMA, "Schema should have 'description' field"
        assert "input_schema" in SUMMARY_EXTRACTOR_SCHEMA, "Schema should have 'input_schema' field"

    def test_schema_name(self):
        """Test that schema has correct tool name"""
        assert SUMMARY_EXTRACTOR_SCHEMA["name"] == "extract_summary_structure", (
            "Tool name should be 'extract_summary_structure'"
        )

    def test_schema_has_actors_field(self):
        """Test that schema includes actors array with required structure"""
        input_schema = SUMMARY_EXTRACTOR_SCHEMA["input_schema"]
        properties = input_schema["properties"]

        assert "actors" in properties, "Schema should include 'actors' field"
        assert properties["actors"]["type"] == "array", "actors should be an array"

        # Check actor item structure
        actor_item = properties["actors"]["items"]
        assert actor_item["type"] == "object", "Each actor should be an object"

        # Check required actor properties
        actor_props = actor_item["properties"]
        assert "name" in actor_props, "Actor should have 'name' field"
        assert "role" in actor_props, "Actor should have 'role' field"
        assert "relationships" in actor_props, "Actor should have 'relationships' field"
        assert "emotional_state" in actor_props, "Actor should have 'emotional_state' field"

        # Check that relationships is an array of strings
        assert actor_props["relationships"]["type"] == "array", "relationships should be an array"
        assert actor_props["relationships"]["items"]["type"] == "string", (
            "relationship items should be strings"
        )

    def test_schema_has_point_of_conflict_field(self):
        """Test that schema includes point_of_conflict with primary and secondary"""
        input_schema = SUMMARY_EXTRACTOR_SCHEMA["input_schema"]
        properties = input_schema["properties"]

        assert "point_of_conflict" in properties, "Schema should include 'point_of_conflict' field"
        conflict = properties["point_of_conflict"]
        assert conflict["type"] == "object", "point_of_conflict should be an object"

        # Check nested properties
        conflict_props = conflict["properties"]
        assert "primary" in conflict_props, "point_of_conflict should have 'primary' field"
        assert conflict_props["primary"]["type"] == "string", "primary should be a string"

        assert "secondary" in conflict_props, "point_of_conflict should have 'secondary' field"
        assert conflict_props["secondary"]["type"] == "array", "secondary should be an array"
        assert conflict_props["secondary"]["items"]["type"] == "string", (
            "secondary items should be strings"
        )

    def test_schema_has_general_details_field(self):
        """Test that schema includes general_details with all required sub-fields"""
        input_schema = SUMMARY_EXTRACTOR_SCHEMA["input_schema"]
        properties = input_schema["properties"]

        assert "general_details" in properties, "Schema should include 'general_details' field"
        details = properties["general_details"]
        assert details["type"] == "object", "general_details should be an object"

        # Check all required sub-fields
        details_props = details["properties"]
        assert "timeline_markers" in details_props, "general_details should have 'timeline_markers'"
        assert details_props["timeline_markers"]["type"] == "array", "timeline_markers should be an array"

        assert "location_context" in details_props, "general_details should have 'location_context'"
        assert details_props["location_context"]["type"] == "array", "location_context should be an array"

        assert "communication_history" in details_props, "general_details should have 'communication_history'"
        assert details_props["communication_history"]["type"] == "array", "communication_history should be an array"

        assert "emotional_atmosphere" in details_props, "general_details should have 'emotional_atmosphere'"
        assert details_props["emotional_atmosphere"]["type"] == "string", (
            "emotional_atmosphere should be a string"
        )

    def test_schema_has_missing_info_field(self):
        """Test that schema includes missing_info array"""
        input_schema = SUMMARY_EXTRACTOR_SCHEMA["input_schema"]
        properties = input_schema["properties"]

        assert "missing_info" in properties, "Schema should include 'missing_info' field"
        assert properties["missing_info"]["type"] == "array", "missing_info should be an array"
        assert properties["missing_info"]["items"]["type"] == "string", (
            "missing_info items should be strings"
        )

    def test_schema_required_fields(self):
        """Test that all top-level fields are marked as required"""
        input_schema = SUMMARY_EXTRACTOR_SCHEMA["input_schema"]
        required = input_schema["required"]

        assert "actors" in required, "actors should be required"
        assert "point_of_conflict" in required, "point_of_conflict should be required"
        assert "general_details" in required, "general_details should be required"
        assert "missing_info" in required, "missing_info should be required"