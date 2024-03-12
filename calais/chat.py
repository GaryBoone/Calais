"""
Chat module to interact with the OpenAI API.
"""

import time
import os
import concurrent.futures
from enum import Enum

from typing import Any, Iterable, List
from openai import OpenAIError, Stream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

from calais.client import IOpenAIClient
from calais.response import Response
from calais.content_printer import ContentPrinter

CONTENTS_START_MARKER = '"contents": "'
CONTENTS_END_MARKER = '",\n'


class Role(Enum):
    """Enum for the role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


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

    def add_to_conversation(self, role: Role, content: str) -> None:
        """Add a message with a given role to the conversation."""
        msg: ChatCompletionMessageParam
        match role:
            case Role.SYSTEM:
                msg = ChatCompletionSystemMessageParam(content=content, role="system")
            case Role.ASSISTANT:
                msg = ChatCompletionAssistantMessageParam(
                    content=content, role="assistant"
                )
            case Role.USER:
                msg = ChatCompletionUserMessageParam(content=content, role="user")
            case _:
                raise ChatError(f"Invalid role: {role}")
        self.conversation.append(msg)

    def _call_api(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Call the OpenAI API to generate a response."""
        resp = self.client.call_api(messages)
        return resp

    def _process_response_chunk(self, chunk: ChatCompletionChunk) -> tuple[str, bool]:
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

    def _check_returned_chunk(
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

    def _call_gpt_api(
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
            future = executor.submit(self._call_api, messages)
            response = future.result(timeout=self.timeout)

        content_printer = ContentPrinter()
        text: str = ""
        empty_chunk_count: int = 0
        for chunk in response:
            chunk = self._check_returned_chunk(chunk)
            chunk_text, stop = self._process_response_chunk(chunk)
            text += chunk_text
            if print_chunks:
                content_printer.print_chunk(chunk_text)
            if not chunk_text.strip():  # Empty or whitespace only.
                empty_chunk_count += 1
            if stop:  # Stop condition met.
                break

        content_printer.finish()
        return text, empty_chunk_count

    def _handle_retry(self, message: str) -> None:
        """Handle retry logic and messaging."""
        print(message)
        time.sleep(self.retry_delay)

    def _generate_response(
        self, messages: Iterable[ChatCompletionMessageParam], print_chunks: bool
    ) -> Response:
        """
        Generate a response from the OpenAI API. Retry on failure up to
        self.max_retries.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                text, empty_chunk_count = self._call_gpt_api(messages, print_chunks)
                if empty_chunk_count > self.max_empty_chunks:
                    self._handle_retry("Received too many empty chunks. Retrying...")
                else:
                    try:
                        # Now that we have a complete response, we can parse
                        # the JSON and return it as a Response object.
                        return Response.from_json(text)
                    except ValueError as e:
                        self._handle_retry(f"Error occurred. Retrying... ({e})")

            except (OpenAIError, concurrent.futures.TimeoutError) as e:
                self._handle_retry(f"Error occurred. Retrying... ({e})")
            retries += 1

        raise ChatError("Failed to receive a response from OpenAI.")

    def call_gpt4(self, prompt: str, print_chunks: bool) -> Response:
        """Call the OpenAI API and accumulate the response chunks."""
        self.add_to_conversation(Role.USER, prompt)
        return self._generate_response(self.conversation, print_chunks)
