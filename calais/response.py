"""This module contains the Response class, which represents the response from the OpenAI API."""

from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from typing import Optional


@dataclass
class Response:
    """Represents a response from the OpenAI API."""

    content: Optional[str]
    command: Optional[str]
    error: Optional[str]

    def to_json(self):
        """Convert the Response object to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> Response:
        """Deserialize JSON string into a Response object."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON string") from exc

        content = data.get("content")  # Can be None.
        command = data.get("command")  # Can be None.
        error = data.get("error")
        return cls(content, command, error)
