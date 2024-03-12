"""Tests for the ContentPrinter class."""

import pytest
from calais.content_printer import ContentPrinter


@pytest.fixture
def printer():
    """Return a ContentPrinter instance."""
    return ContentPrinter()


# pylint: disable=redefined-outer-name
# pylint: disable=protected-access


class TestInitMethod:
    """Tests for the __init__ method."""

    def test_init(self, printer):
        """Test that __init__ intializes."""
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == ""
        assert printer.something_printed is False


class TestPrintChunkMethod:
    """Tests for the print_chunk method."""

    def test_print_chunk_accumulates_chunk_text(self, printer):
        """Test that print_chunk accumulates the incoming chunk text."""
        printer.print_chunk("test chunk")
        assert printer.accumulated_chunk == "test chunk"

    def test_print_chunk_calls_start_printing_content_if_not_printing(
        self, printer, mocker
    ):
        """Test that print_chunk calls _start_printing_content if not printing."""
        printer.printing_contents = False
        mocker.patch.object(printer, "_start_printing_content")
        printer.print_chunk("test chunk")
        printer._start_printing_content.assert_called_once()

    def test_print_chunk_calls_continue_printing_content_if_printing(
        self, printer, mocker
    ):
        """Test that print_chunk calls _continue_printing_content if printing."""
        printer.printing_contents = True
        mocker.patch.object(printer, "_continue_printing_content")
        printer.print_chunk("test chunk")
        printer._continue_printing_content.assert_called_once()


class TestPrintUnescapedChunk:
    """Tests for the print_unescaped_chunk function."""

    test_data = [
        ("Hello\\nWorld", "Hello\nWorld"),
        ("Hello\\tWorld", "Hello\tWorld"),
        ("Hello \\'World\\'", "Hello 'World'"),
        ("Hello\\\\World", "Hello\\World"),
    ]

    def test_print_unescaped_chunk_unescapes_and_prints_content(self, printer, capsys):
        """Test that print_unescaped_chunk unescapes the content and prints it."""
        for chunk_text, expected_output in self.test_data:
            printer._print_unescaped_chunk(chunk_text)
            captured = capsys.readouterr()
            assert captured.out == expected_output


class TestStartPrintingContentMethod:
    """Tests for the _start_printing_content method."""

    def test_start_printing_content_prints_contents_when_start_marker_found(
        self, printer, capsys
    ):
        """Test that _start_printing_content prints the contents when the start marker is found."""
        printer.accumulated_chunk = 'prefix "content": " content text " suffix'
        printer._start_printing_content()
        captured = capsys.readouterr()
        assert captured.out == ' content text " suffix'
        assert printer.printing_contents
        assert printer.accumulated_chunk == ""

    def test_start_printing_content_prints_contents_when_start_and_end_markers_found(
        self, printer, capsys
    ):
        """Test that _start_printing_content prints the contents when both start and end markers are found."""
        printer.accumulated_chunk = 'prefix "content": "content text",\n more text '
        printer._start_printing_content()
        captured = capsys.readouterr()
        assert captured.out == "content text"
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == "\n more text "

    def test_start_printing_content_does_not_print_if_start_marker_not_found(
        self, printer, capsys
    ):
        """Test that _start_printing_content does not print if the start marker is not found."""
        printer.accumulated_chunk = 'prefix "content:  content text " suffix'
        printer._start_printing_content()
        captured = capsys.readouterr()
        assert not captured.out
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == 'prefix "content:  content text " suffix'


class TestContinuePrintingContentMethod:
    """Tests for the _continue_printing_content method."""

    def test_continue_printing_content_prints_accumulated_chunk_if_end_marker_not_found(
        self, printer, capsys
    ):
        """Test that _continue_printing_content prints the accumulated chunk if the end marker is not found."""
        printer.accumulated_chunk = 'content text "\n, suffix'
        printer._continue_printing_content()
        captured = capsys.readouterr()
        assert captured.out == 'content text "\n, suffix'
        assert printer.printing_contents
        assert printer.accumulated_chunk == ""

    def test_continue_printing_content_prints_up_to_end_marker_if_found(
        self, printer, capsys
    ):
        """Test that _continue_printing_content prints up to the end marker if found."""
        printer.accumulated_chunk = 'content text ",\n suffix'
        printer._continue_printing_content()
        captured = capsys.readouterr()
        assert captured.out == "content text "
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == "\n suffix"


class TestPrintChunkWithSplitMarkers:
    """Tests for the print_chunk method with split markers."""

    def test_print_chunk_with_split_start_marker(self, printer, capsys):
        """Test that print_chunk handles a split start marker correctly."""
        printer.print_chunk('prefix "cont')
        printer.print_chunk('ent": "content text " suffix')
        captured = capsys.readouterr()
        assert captured.out == 'content text " suffix'
        assert printer.printing_contents
        assert printer.accumulated_chunk == ""

    def test_print_chunk_with_split_end_marker(self, printer, capsys):
        """Test that print_chunk handles a split end marker at |: '"|,'."""
        printer.printing_contents = True
        printer.print_chunk('content text "')
        printer.print_chunk(",\n suffix")
        captured = capsys.readouterr()
        assert captured.out == "content text "
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == "\n suffix"

    def test_print_chunk_with_split_non_end_marker1(self, printer, capsys):
        """Test that print_chunk handles what looks like a split end marker."""
        printer.printing_contents = True
        printer.print_chunk('content text "')  # First char of end marker,
        printer.print_chunk(" suffix")  # but not the last one. So no end marker.
        captured = capsys.readouterr()
        assert captured.out == 'content text " suffix'
        assert printer.printing_contents is True
        assert printer.accumulated_chunk == ""

    def test_print_chunk_with_split_start_and_end_markers(self, printer, capsys):
        """Test that print_chunk handles split start and end markers correctly."""
        printer.print_chunk('prefix "content"')
        printer.print_chunk(': "')
        printer.print_chunk('content text ",')
        printer.print_chunk("\n suffix")
        captured = capsys.readouterr()
        assert captured.out == "content text "
        assert printer.printing_contents is False
        assert printer.accumulated_chunk == "\n suffix"
