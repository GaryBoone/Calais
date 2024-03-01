"""
Chat module to interact with the OpenAI API.
"""

import time
import os
import concurrent.futures

from typing import Any, Iterable, List, Optional
from openai import OpenAIError, Stream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

from client import IOpenAIClient


class ChatError(Exception):
    """Exception raised for unretryable errors in the Chat class."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Chat:
    """A class to interact with the OpenAI API and manage a conversation."""

    def __init__(
        self,
        client: IOpenAIClient,
        retries: int,
        timeout: int,
        retry_delay: int,
        max_empty_chunks: int,
    ) -> None:
        self.client: IOpenAIClient = client
        self.max_retries: int = retries
        self.timeout: int = timeout
        self.retry_delay: int = retry_delay
        self.max_empty_chunks: int = max_empty_chunks
        self.conversation: List[ChatCompletionMessageParam] = []

    def add_to_conversation(self, role: str, content: str) -> None:
        """Add a message with a given role to the conversation."""
        msg: ChatCompletionMessageParam
        match role:
            case "system":
                msg = ChatCompletionSystemMessageParam(content=content, role="system")
            case "assistant":
                msg = ChatCompletionAssistantMessageParam(
                    content=content, role="assistant"
                )
            case "user":
                msg = ChatCompletionUserMessageParam(content=content, role="user")
            case _:
                raise ChatError(f"Invalid role: {role}")
        self.conversation.append(msg)

    def call_api(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Call the OpenAI API to generate a response."""
        return self.client.call_api(messages)

    def get_api_key(self) -> str:
        """Safely retrieve the OPENAI_API_KEY from the environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ChatError("OPENAI_API_KEY environment variable is not set.")
        return api_key

    def process_response_chunk(self, chunk: ChatCompletionChunk) -> tuple[str, bool]:
        """
        Process a single response chunk. Return the chunk as text, empty if the
        content was return as None. Also return True if the finish_reason was
        "stop", else False if the max_tokens was reached.

        Note that according to the OpenAI API documentation, the content and
        finish_reason are not exclusive. That is, there can be content if there
        is a non-None finish_reason.
        https://platform.openai.com/docs/guides/text-generation/completions-api
        """
        content = chunk.choices[0].delta.content
        if content is None:
            content = ""
        match (reason := chunk.choices[0].finish_reason):
            case "length":
                raise ChatError("stopped because max_tokens reached")
            case "stop":
                return content, True  # Signal to stop processing.
            case None:
                pass  # Do nothing, continue processing.
            case _:
                raise ChatError(f"unexpected completion reason: {reason}")
        return content, False

    def check_returned_chunk(
        self, chunk: tuple[str, Any] | ChatCompletionChunk
    ) -> ChatCompletionChunk:
        """
        Check if chunk is of expected ChatCompletionChunk type. Return
        the chunk as a ChatCompletionChunk else raise an error.
        """
        if isinstance(chunk, ChatCompletionChunk):
            return chunk
        elif isinstance(chunk, tuple) and len(chunk) == 2:
            # Handle tuple[str, Any] type chunk here, possibly a status
            # message or error.
            raise ChatError(
                f"Received a tuple instead of a ChatCompletionChunk: {chunk}"
            )
        else:
            raise ChatError(f"Received an unexpected chunk type: {type(chunk)}")

    def call_gpt_api(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        print_chunks: bool = False,
    ) -> tuple[str, int]:
        """
        Attempt to call the API and process the response. Return the
        response text and the number of empty chunks.

        If print_chunks is True, print each chunk immediately as it is
        received.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.call_api, messages)
            response = future.result(timeout=self.timeout)

        text: str = ""
        empty_chunk_count: int = 0
        for chunk in response:
            chunk = self.check_returned_chunk(chunk)
            chunk_text, stop = self.process_response_chunk(chunk)
            if print_chunks:
                print(chunk_text, end="")
            if not chunk_text.strip():  # Empty or whitespace only.
                empty_chunk_count += 1
            text += chunk_text
            if stop:  # Stop condition met.
                break

        return text, empty_chunk_count

    def handle_retry(self, message: str) -> None:
        """Handle retry logic and messaging."""
        print(message)
        time.sleep(self.retry_delay)

    def generate_response(
        self, messages: Iterable[ChatCompletionMessageParam], print_chunks: bool
    ) -> str:
        """
        Generate a response from the OpenAI API. Retry on failure up to
        self.max_retries.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                text, empty_chunk_count = self.call_gpt_api(messages, print_chunks)
                if empty_chunk_count > self.max_empty_chunks:
                    self.handle_retry("Received too many empty chunks. Retrying...")
                else:
                    return text

            except (OpenAIError, concurrent.futures.TimeoutError) as e:
                self.handle_retry(f"Error occurred. Retrying... ({e})")
            retries += 1

        raise ChatError("Failed to receive a response from OpenAI.")

    def call_gpt4(self, prompt: str, print_chunks: bool) -> str:
        """Call the OpenAI API and accumulate the response chunks."""
        self.add_to_conversation("user", prompt)
        return self.generate_response(self.conversation, print_chunks)
