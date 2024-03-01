"""
The Client module contains the IOpenAIClient interface, including real and test
implementations.
"""

from typing import Iterable, Protocol
from openai import OpenAI, Stream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
)


class IOpenAIClient(Protocol):
    """
    Defines the interface for calling the OpenAI API, either returning a single
    completion or a stream of chat completion chunks.
    """

    def call_api(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Call the OpenAI API with the given messages."""


class OpenAIClient(IOpenAIClient):
    """This is the real implementation of the IOpenAIClient interface."""

    def __init__(self, api_key: str, model: str, max_tokens: int, temperature: float):
        self.client = OpenAI(api_key=api_key)
        self.model: str = model
        self.max_tokens: int = max_tokens
        self.temperature: float = temperature

    def call_api(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Call the streaming OpenAI API with the given messages."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,
        )
