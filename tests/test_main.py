"""Tests for the main module."""

import re
from unittest.mock import patch, MagicMock
import pytest

import calais.main


# Group tests for review_command function
class TestReviewCommand:
    """Test the review_command function."""

    def test_review_command_with_cleaning(self) -> None:
        """Test review_command with a command that has extra spaces."""
        command = "ls  -la"
        expected_command = "ls -la"
        assert calais.main.review_command(command) == expected_command

    def test_review_command_without_cleaning(self) -> None:
        """Test review_command with a command that doesn't need cleaning."""
        command = "ls -la"
        assert calais.main.review_command(command) == command

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf /",
            "rm -rf / ",
            "rm -fr / ",
            "bash rm -fr / ",
            "sh rm -rf / && echo 'hacked'",
            "dd if=/dev/zero of=/dev/sda2",
            "echo ' ' > /dev/sda",
            "mkfs.ext2 /dev/sda",
            "mkfs.ext3 /dev/sda",
            "mkfs.ext4 /dev/sda",
            "chmod -R 777 / ",
            ":(){ :|:& };:",
            "history | sh ",
            " format c: /q ",
        ],
    )
    def test_review_command_with_unsafe_command(self, command) -> None:
        """Test review_command with various unsafe commands."""
        with patch("sys.exit") as mock_exit:
            calais.main.review_command(command)
            mock_exit.assert_called_once_with(1)


class TestCheckInput:
    """Test the check_input function."""

    @pytest.fixture
    def mock_match(self) -> re.Match:
        """Fixture to create a mock re.Match object."""
        match = MagicMock(spec=re.Match)
        match.group.return_value = "test_pattern"
        return match

    def test_check_input_safe(self, mock_match) -> None:
        """Test check_input with safe user input."""
        with patch("builtins.input", return_value="safe_input") as mock_input:
            result = calais.main.check_input(mock_match)
            mock_input.assert_called_once_with("Enter the value for test_pattern: ")
            assert result == "safe_input"

    def test_check_input_unsafe_root(self, mock_match) -> None:
        """Test check_input with unsafe user input targeting root directory."""
        with patch("builtins.input", return_value="/"), patch("sys.exit") as mock_exit:
            calais.main.check_input(mock_match)
            mock_exit.assert_called_once_with(1)

    def test_check_input_unsafe_root_wildcard(self, mock_match) -> None:
        """Test check_input with unsafe user input targeting root directory with wildcard."""
        with patch("builtins.input", return_value="/*"), patch("sys.exit") as mock_exit:
            calais.main.check_input(mock_match)
            mock_exit.assert_called_once_with(1)
