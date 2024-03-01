"""Tests for the Client class."""

import pytest

from openai.types.chat.chat_completion_chunk import (
    Choice,
    ChoiceDelta,
    ChatCompletionChunk,
)

from client import IOpenAIClient
from chat import Chat

# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_openai_client(mocker):
    """Create a mock IOpenAIClient."""
    return mocker.create_autospec(IOpenAIClient, instance=True)


@pytest.fixture
def chat_service(mock_openai_client):
    """Inject the mock IOpenAIClient into Chat."""
    return Chat(mock_openai_client, 1, 1, 1, 1)


@pytest.fixture
def make_mock_chunk(content, finish_reason=None):
    """Create a single chunk with the given content and finish reason."""
    return ChatCompletionChunk(
        id="fake_id",
        choices=[
            Choice(
                delta=ChoiceDelta(content=content, role="assistant"),
                index=0,
                finish_reason=finish_reason,
            )
        ],
        model="gpt-4",
        created=12345678,
        object="chat.completion.chunk",
    )


class ChatServiceTestHelper:
    """Helper class for testing the Chat service."""

    def test_chat_call_api_single_chunk(self, mock_openai_client, chat_service):
        """Test a single chunk response."""
        mock_chunk = make_mock_chunk("single_chunk", None)
        mock_openai_client.call_api.return_value = iter([mock_chunk])

        test_message = {"role": "user", "content": "Hello, single chunk!"}
        result_stream = chat_service.call_api([test_message])

        chunk = next(result_stream)
        assert chunk.choices[0].delta.content == "single_chunk"
        assert chunk.choices[0].finish_reason is None

    def test_chat_call_api_multiple_chunks(self, mock_openai_client, chat_service):
        """Test a multiple chunk response."""
        mock_chunks = [
            make_mock_chunk("chunk0"),
            make_mock_chunk("chunk1"),
            make_mock_chunk("chunk2", "stop"),
        ]
        mock_openai_client.call_api.return_value = iter(mock_chunks)

        test_messages = [
            {"role": "system", "content": "Test system message"},
            {"role": "user", "content": "Hello, world!"},
        ]

        result_stream = chat_service.call_api(test_messages)

        expected_contents = [("chunk0", None), ("chunk1", None), ("chunk2", "stop")]
        for (expected_content, expected_finish_reason), chunk in zip(
            expected_contents, result_stream
        ):
            assert chunk.choices[0].delta.content == expected_content
            assert chunk.choices[0].finish_reason == expected_finish_reason
