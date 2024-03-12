"""Module for ContentPrinter class."""

import codecs

CONTENTS_START_MARKER = '"content": "'
CONTENTS_END_MARKER = '",'


class ContentPrinter:
    """
    ContentPrinter prints chunks if they're in the 'contents' JSON stream. It
    prints the content of the JSON value when the 'contents' key is found,
    without printing the key or JSON syntax. Therefore, it is useful for
    printing the contents field of the structured response from the OpenAI API,
    while streaming, even though the contents are returned within a JSON
    structure.

    It works by watching for the start and end markers of the "contents"
    section in the JSON stream. When it sees the start marker, it starts
    printing the content. When it sees the end marker, it stops printing the
    content.

    The chunks are accumulated in case the start and end markers are split
    across chunks.
    """

    def __init__(self):
        self.printing_contents = False
        self.accumulated_chunk = ""
        self.something_printed = False

    def print_chunk(self, chunk_text: str) -> None:
        """Print chunks if we've detected the start marker."""
        self.accumulated_chunk += chunk_text
        if self.printing_contents:
            self._continue_printing_content()
        else:
            self._start_printing_content()

    def finish(self) -> None:
        """Print a newline if something was printed.

        Call after a GPT request to ensure the next prompt is on a new
        line.
        """
        if self.something_printed:
            print()

    def _print_unescaped_chunk(self, chunk_text: str) -> None:
        """Print the given chunk but undo escaped characters."""
        try:
            unescaped = codecs.decode(chunk_text, "unicode_escape")
        except UnicodeDecodeError:
            unescaped = chunk_text
        if unescaped:
            print(unescaped, end="", flush=True)
            self.something_printed = True

    def _continue_printing_content(self) -> None:
        """Print chunks, watching for the end marker."""
        if CONTENTS_END_MARKER in self.accumulated_chunk:
            end_index = self.accumulated_chunk.index(CONTENTS_END_MARKER)
            self._print_unescaped_chunk(self.accumulated_chunk[:end_index])
            self.accumulated_chunk = self.accumulated_chunk[end_index:]
            if len(self.accumulated_chunk) >= len(CONTENTS_END_MARKER):
                self.accumulated_chunk = self.accumulated_chunk[
                    len(CONTENTS_END_MARKER) :
                ]
                self.printing_contents = False
        else:
            # The end marker may be split across chunks, so look for a
            # partial match.
            potential_end_index = -1
            for i in range(len(CONTENTS_END_MARKER)):
                if self.accumulated_chunk.endswith(CONTENTS_END_MARKER[: i + 1]):
                    potential_end_index = len(self.accumulated_chunk) - (i + 1)
                    break
            if potential_end_index != -1:
                # If we found a partial match, print up to the match and
                # leave the partial end marker in the chunk buffer.
                self._print_unescaped_chunk(
                    self.accumulated_chunk[:potential_end_index]
                )
                self.accumulated_chunk = self.accumulated_chunk[potential_end_index:]
                return

            if self.accumulated_chunk.endswith("\\"):
                self._print_unescaped_chunk(self.accumulated_chunk[:-1])
                self.accumulated_chunk = "\\"
                return

            self._print_unescaped_chunk(self.accumulated_chunk)
            self.accumulated_chunk = ""
            self.printing_contents = True

    def _start_printing_content(self) -> None:
        """Look for the start of the content marker and print the contents."""
        if CONTENTS_START_MARKER in self.accumulated_chunk:
            start_index = self.accumulated_chunk.index(CONTENTS_START_MARKER) + len(
                CONTENTS_START_MARKER
            )
            end_index = self.accumulated_chunk.find(CONTENTS_END_MARKER, start_index)
            if end_index != -1:
                self._print_unescaped_chunk(
                    self.accumulated_chunk[start_index:end_index]
                )
                self.accumulated_chunk = self.accumulated_chunk[
                    end_index + len(CONTENTS_END_MARKER) :
                ]
                self.printing_contents = False
            else:
                self._print_unescaped_chunk(self.accumulated_chunk[start_index:])
                self.accumulated_chunk = ""
                self.printing_contents = True
