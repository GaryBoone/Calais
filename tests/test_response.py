"""Tests for the Response class."""

from typing import Dict, Any
import pytest

from calais.response import Response


class TestResponse:
    """Tests for the Response class."""

    def test_init(self) -> None:
        """Test the initialization of the Response class."""
        response = Response(None, None, None)
        assert response.content is None
        assert response.command is None
        assert response.error is None

        response = Response("Hello, how can I assist you?", None, None)
        assert response.content == "Hello, how can I assist you?"
        assert response.command is None
        assert response.error is None

        response = Response(None, None, "This is an error.")
        assert response.content is None
        assert response.command is None
        assert response.error == "This is an error."

    def test_to_json(self) -> None:
        """Test the serialization of Response objects into JSON strings."""
        test_cases: Dict[str, Dict[str, Any]] = {
            "conversation": {
                "response_obj": Response("Hello, how can I assist you?", None, None),
                "expected_json": '{"content": "Hello, how can I assist you?", "command": null, "error": null}',
            },
            "command_with_explanation": {
                "response_obj": Response("-l is long format", "ls -l", None),
                "expected_json": '{"content": "-l is long format", "command": "ls -l", "error": null}',
            },
            "command_without_explanation": {
                "response_obj": Response(None, "ls -l", None),
                "expected_json": '{"content": null, "command": "ls -l", "error": null}',
            },
            "error": {
                "response_obj": Response(None, None, "error desc"),
                "expected_json": '{"content": null, "command": null, "error": "error desc"}',
            },
        }

        for _, data in test_cases.items():
            result_json = data["response_obj"].to_json()
            assert result_json == data["expected_json"]

    def test_from_json(self) -> None:
        """Test the deserialization of valid JSON strings into Response objects."""
        test_cases: Dict[str, Dict[str, Any]] = {
            "conversation": {
                "json_str": '{"command": null, "content": "Hello, how can I assist you?", "error": null}',
                "expected_content": "Hello, how can I assist you?",
                "expected_command": None,
                "expected_error": None,
            },
            "command_with_explanation": {
                "json_str": '{"content": "-l is long format", "command": "ls -l", "error": null}',
                "expected_content": "-l is long format",
                "expected_command": "ls -l",
                "expected_error": None,
            },
            "command_without_explanation": {
                "json_str": '{"content": null, "command": "ls -l", "error": null}',
                "expected_content": None,
                "expected_command": "ls -l",
                "expected_error": None,
            },
            "error": {
                "json_str": '{"content": null, "command": null, "error": "error desc"}',
                "expected_content": None,
                "expected_command": None,
                "expected_error": "error desc",
            },
        }

        for _, data in test_cases.items():
            response = Response.from_json(data["json_str"])
            assert response.content == data["expected_content"]
            assert response.command == data["expected_command"]
            assert response.error == data["expected_error"]

    def test_from_json_invalid_json(self) -> None:
        """Test when an invalid JSON string is provided."""
        json_str = "invalid JSON string"
        with pytest.raises(ValueError, match="Invalid JSON string"):
            Response.from_json(json_str)
