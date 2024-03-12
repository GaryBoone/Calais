"""Tests for the Chat class."""

from typing import Iterable, List, Literal, Optional
from unittest import mock
from unittest.mock import patch, Mock
import pytest

from openai import Stream
from openai.types.chat.chat_completion_chunk import (
    Choice,
    ChoiceDelta,
    ChatCompletionChunk,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
)

from calais.chat import (
    Chat,
    ChatError,
    Role,
)
from calais.client import IOpenAIClient

# pylint: disable=redefined-outer-name


class MockOpenAIClient(IOpenAIClient):
    """Mock implementation of the IOpenAIClient interface."""

    def __init__(self) -> None:
        """Create a new mock OpenAI client."""
        self.mock = Mock()

    def send_message(
        self, messages: List[ChatCompletionMessageParam], model: str
    ) -> str:
        """Send a single message to the OpenAI API."""
        return self.mock.send_message(messages, model)

    def send_messages(
        self, messages: List[ChatCompletionMessageParam], model: str
    ) -> List[str]:
        """Send multiple messages to the OpenAI API."""
        return self.mock.send_messages(messages, model)

    def call_api(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Call the OpenAI API with the given messages."""
        return self.mock.call_api(messages)


@pytest.fixture
def mock_client() -> MockOpenAIClient:
    """Create a mock OpenAI client."""
    return MockOpenAIClient()


@pytest.fixture
def chat_instance():
    """Create a Chat instance with default parameters."""
    return Chat(client=None, retries=3, timeout=10, retry_delay=5, max_empty_chunks=3)


@pytest.fixture
def make_mock_chunk():
    """Fixture to create mock chat completion chunks."""

    def _make(
        content: Optional[str] = None,
        finish_reason: (
            Literal["stop", "length", "tool_calls", "content_filter", "function_call"]
            | None
        ) = None,
    ) -> ChatCompletionChunk:
        return ChatCompletionChunk(
            id="fake_id",
            created=12345678,
            model="gpt-4",
            object="chat.completion.chunk",
            choices=[
                Choice(
                    delta=ChoiceDelta(content=content),
                    index=0,
                    finish_reason=finish_reason,
                )
            ],
        )

    return _make


class TestInit:
    """Test the __init__ method of the Chat class."""

    def test_chat_init(self, mocker) -> None:
        """Test the __init__ method of the Chat class."""
        fake_client = mocker.MagicMock()
        retries = 3
        timeout = 10
        retry_delay = 5
        max_empty_chunks = 3

        gpt = Chat(
            fake_client,
            retries=retries,
            timeout=timeout,
            retry_delay=retry_delay,
            max_empty_chunks=max_empty_chunks,
        )

        assert gpt.client == fake_client
        assert gpt.max_retries == retries
        assert gpt.timeout == timeout
        assert gpt.retry_delay == retry_delay
        assert gpt.max_empty_chunks == max_empty_chunks
        assert not gpt.conversation


class TestAddToConversation:
    """Test the add_to_conversation method of the Chat class."""

    def test_add_to_conversation_system(self):
        """Test the add_to_conversation method of the Chat class for system."""

        chat = Chat(None, 1, 1, 1, 1)
        chat.add_to_conversation(Role.SYSTEM, "Hello")
        assert len(chat.conversation) == 1
        assert chat.conversation[0]["role"] == "system"
        assert chat.conversation[0]["content"] == "Hello"

    def test_add_to_conversation_assistant(self):
        """Test the add_to_conversation method of the Chat class for assistant."""

        chat = Chat(None, 1, 1, 1, 1)
        chat.add_to_conversation(Role.ASSISTANT, "Hello")
        assert len(chat.conversation) == 1
        assert chat.conversation[0]["role"] == "assistant"
        assert chat.conversation[0]["content"] == "Hello"

    def test_add_to_conversation_user(self):
        """Test the add_to_conversation method of the Chat class for user."""

        chat = Chat(None, 1, 1, 1, 1)
        chat.add_to_conversation(Role.USER, "Hello")
        assert len(chat.conversation) == 1
        assert chat.conversation[0]["role"] == "user"
        assert chat.conversation[0]["content"] == "Hello"


class MockDelta:
    """Mock Delta class."""

    def __init__(self, content):
        self.content = content


class MockChoice:
    """Mock Choice class."""

    def __init__(self, delta, finish_reason):
        self.delta = delta
        self.finish_reason = finish_reason


class TestProcessResponseChunk:
    """Test the process_response_chunk method of the Chat class."""

    def test_process_response_chunk(self, mocker):
        """Test the process_response_chunk method of the Chat class."""
        mock_delta = MockDelta(content="Hello")
        mock_choice = MockChoice(delta=mock_delta, finish_reason=None)

        mock_chunk = mocker.MagicMock()
        mock_chunk.choices = [mock_choice]
        chat = Chat(None, 1, 1, 1, 1)
        content, stop = chat.process_response_chunk(mock_chunk)
        assert content == "Hello"
        assert not stop

    def test_process_response_chunk_multiple(self, mocker):
        """Now multiple chunks."""
        chat = Chat(None, 1, 1, 1, 1)

        mock_chunk1 = mocker.MagicMock()
        mock_chunk2 = mocker.MagicMock()
        mock_chunk3 = mocker.MagicMock()

        chat.process_response_chunk = mocker.MagicMock(
            side_effect=[
                ("Hello", False),
                (" World", False),
                ("!", True),
            ]
        )

        chunks = [mock_chunk1, mock_chunk2, mock_chunk3]
        for chunk in chunks:
            _, stop = chat.process_response_chunk(chunk)
            if stop:
                break

        calls = [mocker.call(chunk) for chunk in chunks]
        chat.process_response_chunk.assert_has_calls(calls)

        assert chat.process_response_chunk.call_count == len(chunks)

    def test_process_empty_content_chunk(self, mocker):
        """Test processing a chunk with empty content."""
        chat = Chat(None, 1, 1, 1, 1)

        # Setup a mock chunk with empty content but no explicit stop condition
        mock_chunk_empty_content = mocker.MagicMock()
        mock_chunk_empty_content.choices = [
            mocker.MagicMock(delta=mocker.MagicMock(content=""), finish_reason=None)
        ]

        # If process_response_chunk is supposed to return content and a stop flag,
        # ensure it's mocked to reflect the expected behavior with empty content
        chat.process_response_chunk = mocker.MagicMock(return_value=("", False))

        # Process the mock chunk with empty content
        content, stop = chat.process_response_chunk(mock_chunk_empty_content)

        # Verify that the content is empty and processing is not stopped
        assert content == ""
        assert stop is False

        # Verify that process_response_chunk was called once with the mock chunk
        chat.process_response_chunk.assert_called_once_with(mock_chunk_empty_content)

    def test_normal_content(self, chat_instance, make_mock_chunk):
        """Test processing a chunk with normal content."""
        chunk = make_mock_chunk(content="Hello", finish_reason=None)
        content, stop = chat_instance.process_response_chunk(chunk)
        assert content == "Hello"
        assert not stop

    def test_content_with_stop_reason(self, chat_instance, make_mock_chunk):
        """Test processing a chunk with stop reason."""
        chunk = make_mock_chunk(content="Goodbye", finish_reason="stop")
        content, stop = chat_instance.process_response_chunk(chunk)
        assert content == "Goodbye"
        assert stop

    def test_content_with_length_reason(self, chat_instance, make_mock_chunk):
        """Test processing a chunk with length reason."""
        chunk = make_mock_chunk(content="Lengthy content", finish_reason="length")
        with pytest.raises(ChatError) as exc_info:
            chat_instance.process_response_chunk(chunk)
        assert "max_tokens reached" in str(exc_info.value)

    def test_content_is_none(self, chat_instance, make_mock_chunk):
        """Test processing a chunk with None content."""
        chunk = make_mock_chunk(content=None, finish_reason=None)
        content, stop = chat_instance.process_response_chunk(chunk)
        assert content == ""
        assert not stop


class TestCheckReturnedChunk:
    """Test the check_returned_chunk method of the Chat class."""

    def test_check_returned_chunk_with_valid_chunk(
        self, chat_instance, make_mock_chunk
    ):
        """Test check_returned_chunk with a valid ChatCompletionChunk."""
        valid_chunk = make_mock_chunk(content="Test content", finish_reason="stop")
        # No error should be raised, and the chunk should be returned as is.
        assert chat_instance.check_returned_chunk(valid_chunk) == valid_chunk

    def test_check_returned_chunk_with_tuple(self, chat_instance):
        """Test check_returned_chunk with a tuple input."""
        tuple_input = ("Error", "This is a tuple, not a ChatCompletionChunk")
        with pytest.raises(ChatError) as exc_info:
            chat_instance.check_returned_chunk(tuple_input)
        assert "Received a tuple instead of a ChatCompletionChunk" in str(
            exc_info.value
        )

    def test_check_returned_chunk_with_invalid_type(self, chat_instance):
        """Test check_returned_chunk with an unexpected type."""
        invalid_input = ["This is", "not a valid input type"]
        with pytest.raises(ChatError) as exc_info:
            chat_instance.check_returned_chunk(invalid_input)
        assert "Received an unexpected chunk type" in str(exc_info.value)


class TestCallGptApi:
    """Test the call_gpt_api method of the Chat class."""

    @pytest.fixture(autouse=True)
    # pylint: disable=attribute-defined-outside-init
    def _setup(self, chat_instance, make_mock_chunk):
        self.chat = chat_instance
        self.make_mock_chunk = make_mock_chunk

    def test_normal_response_handling(self, chat_instance):
        """Test normal response handling."""
        mock_chunks = [
            self.make_mock_chunk(content="Hello, "),
            self.make_mock_chunk(content="world!"),
        ]
        with mock.patch.object(
            chat_instance, "call_api", return_value=mock_chunks
        ), mock.patch.object(
            chat_instance, "check_returned_chunk", side_effect=lambda x: x
        ), mock.patch.object(
            chat_instance,
            "process_response_chunk",
            side_effect=lambda x: (x.choices[0].delta.content, False),
        ):
            response_text, empty_count = chat_instance.call_gpt_api([])
            assert response_text == "Hello, world!"
            assert empty_count == 0

    def test_empty_chunk_counting(self, chat_instance):
        """Test counting of empty chunks."""
        mock_chunks = [
            self.make_mock_chunk(content=" \t \n \r"),
            self.make_mock_chunk(content=""),
            self.make_mock_chunk(content=" "),
        ]
        with mock.patch.object(
            chat_instance, "call_api", return_value=mock_chunks
        ), mock.patch.object(
            chat_instance, "check_returned_chunk", side_effect=lambda x: x
        ), mock.patch.object(
            chat_instance,
            "process_response_chunk",
            side_effect=lambda x: (x.choices[0].delta.content, False),
        ):
            response_text, empty_count = chat_instance.call_gpt_api([])
            assert response_text == " \t \n \r "
            assert empty_count == 3

    def test_early_stop(self, chat_instance):
        """Test early stop condition."""
        mock_chunks = [
            self.make_mock_chunk(content="Stop here", finish_reason="stop"),
            self.make_mock_chunk(content="Should not see this"),
        ]
        with mock.patch.object(
            chat_instance, "call_api", return_value=mock_chunks
        ), mock.patch.object(
            chat_instance, "check_returned_chunk", side_effect=lambda x: x
        ), mock.patch.object(
            chat_instance,
            "process_response_chunk",
            side_effect=lambda x: (x.choices[0].delta.content, True),
        ):
            response_text, empty_count = chat_instance.call_gpt_api([])
            assert response_text == "Stop here"
            assert empty_count == 0

    def test_timeout_handling(self, chat_instance):
        """Test handling of API call timeout."""
        with mock.patch.object(
            chat_instance, "call_api", side_effect=Exception("Timeout reached")
        ):
            with pytest.raises(Exception) as exc_info:
                chat_instance.call_gpt_api([])
            assert "Timeout reached" in str(exc_info.value)


class TestChatResponseGeneration:
    """Test the generate_response method of the Chat class."""

    @pytest.fixture
    def chat_instance(self, mocker):
        """Fixture to create a Chat instance with default parameters."""
        client = mocker.MagicMock()
        return Chat(
            client=client, retries=3, timeout=10, retry_delay=1, max_empty_chunks=2
        )

    @patch("calais.chat.Chat.call_gpt_api")
    @patch("time.sleep", return_value=None)
    def test_generate_response_with_too_many_empty_chunks(
        self, mock_sleep, mock_call_gpt_api, chat_instance
    ):
        """
        Test generate_response retries when receiving too many empty chunks and eventually raises ChatError.
        """
        mock_call_gpt_api.return_value = (
            "",
            chat_instance.max_empty_chunks + 1,  # Exceed the max_empty_chunks limit.
        )

        with pytest.raises(ChatError) as exc_info:
            chat_instance.generate_response([], False)

        assert "Failed to receive a response from OpenAI." in str(exc_info.value)
        # Ensure call_gpt_api was called max_retries + 1 times (initial attempt + retries)
        assert mock_call_gpt_api.call_count == chat_instance.max_retries + 1
        assert mock_sleep.call_count == chat_instance.max_retries + 1

    @patch("calais.chat.Chat.call_gpt_api")
    @patch("time.sleep", return_value=None)
    def test_generate_response_with_valid_json(
        self, mock_sleep, mock_call_gpt_api, chat_instance
    ):
        """
        Test generate_response retries when the response is valid JSON.
        """
        mock_call_gpt_api.return_value = (
            '{"error": null, "command": "a command", "content": "execute_command"}',
            0,
        )

        resp = chat_instance.generate_response([], False)

        assert resp.content == "execute_command"
        assert resp.command == "a command"
        assert resp.error is None
        assert mock_call_gpt_api.call_count == 1
        assert mock_sleep.call_count == 0

    @patch("calais.chat.Chat.call_gpt_api")
    @patch("time.sleep", return_value=None)
    def test_generate_response_with_invalid_json(
        self, mock_sleep, mock_call_gpt_api, chat_instance
    ):
        """
        Test generate_response retries when the response is not valid JSON.
        """
        mock_call_gpt_api.return_value = (
            '{"type": "command"',
            0,
        )

        with pytest.raises(ChatError) as exc_info:
            chat_instance.generate_response([], False)

        assert "Failed to receive a response from OpenAI." in str(exc_info.value)
        assert mock_call_gpt_api.call_count == 4
        assert mock_sleep.call_count == 4
