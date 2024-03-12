"""
Main module for calais. This module initializes the GPT-4 model, sends
prompts to the model, and processes the responses.
"""

import os
import platform
import re
import subprocess
import sys
from typing_extensions import NoReturn

from calais.chat import Chat, Role
from calais.client import OpenAIClient
from calais.system_prompt import COMMAND_SYSTEM_PROMPT

# GPT-4 parameters:
MODEL = "gpt-4"
MAX_TOKENS = 4096
TEMPERATURE = 0.3

# Chat parameters:
MAX_RETRIES = 3
RETRY_DELAY = 5  # Seconds
TIMEOUT = 60  # Seconds
# GPT can sometimes stall, returning empty chunks. Count these and retry if
# the count exceeds this value.
MAX_EMPTY_CHUNKS = 100

# Simple safety checks:
# The commands returned from GPT-4 are checked against this list of unsafe
# strings. If a command contains any of these strings, the program will exit.
# This is a limited, non-exhaustive list. It doesn't catch all unsafe commands
# nor does it handle whitespace or parameter ordering variations. It only
# catches some simple cases. Use with caution! Always review the command before
# running it.
UNSAFE_STRINGS = [
    "rm -r -f /",
    "rm -rf /",
    "rm -fr /",
    "rm -rf --no-preserve-root",
    "rm -fr --no-preserve-root",
    "rm --no-preserve-root -rf ",
    "rm --no-preserve-root -fr ",
    "> /dev/sda",
    "of=/dev/sda",
    "mkfs.ext2 /dev/sda",
    "mkfs.ext3 /dev/sda",
    "mkfs.ext4 /dev/sda",
    "chmod -R 777 /",
    ":(){ :|:& };:",
    "history | ",
    "format c: /q",
    "truncate -s 0",
]


def initialize_gpt(system_prompt: str) -> Chat:
    """Initialize the GPT-4 model

    Check for the API key, create a chat object, and set the system prompt.
    """
    if "OPENAI_API_KEY" not in os.environ:
        print(
            "Please set the OPENAI_API_KEY environment variable to your OpenAI API key."
        )
        sys.exit(1)
    chat_client = OpenAIClient(
        os.environ["OPENAI_API_KEY"],
        MODEL,
        MAX_TOKENS,
        TEMPERATURE,
    )
    gpt = Chat(
        chat_client,
        MAX_RETRIES,
        TIMEOUT,
        RETRY_DELAY,
        MAX_EMPTY_CHUNKS,
    )
    gpt.add_to_conversation(Role.SYSTEM, system_prompt)
    return gpt


def do_command(response):
    """Handle a command response from GPT-4.

    The response content will have been printed by the stream handler.
    """
    command = process_command(response.command)
    command = review_command(command)
    print(f"Command: `{command}`")
    # The stream handler will have printed the explanation, if any, in
    # the contents.
    user_input = input("[r]un,(e)xplain],(q)uit, or continue chatting: ")

    match user_input.lower():
        case "" | "R" | "r":
            try:
                subprocess.run(command, shell=True, check=True)
            except KeyboardInterrupt:
                print("Execution interrupted by user. Exiting.")
            finally:
                sys.exit(0)
        case "q" | "quit" | "exit":
            sys.exit(0)
        case "e" | "ex" | "explain":
            user_prompt = f"Explain the command `{command}`. Return the command in the command field and the explanation in the content field."
            return user_prompt
        case _:
            user_prompt = input("\n> Prompt ([q] to quit): ")
            if user_prompt.lower() in ["", "q", "quit", "exit"]:
                sys.exit(0)
            return user_prompt


def do_content_prompt():
    """Handle a content response from GPT-4.

    The response content will have been printed by the stream handler.
    """
    user_prompt = input("[q]uit, or continue chatting: ")

    match user_prompt.lower():
        case "" | "q" | "quit" | "exit":
            sys.exit(0)
        case _:
            return user_prompt


def converse(gpt: Chat, user_prompt: str) -> NoReturn:
    """Chat with GPT-4, looping until the user decides to stop."""
    while True:
        response = gpt.call_gpt4(user_prompt, True)
        if response.error:
            print("GPT-4 returned an error:")
            print(f"{response.error}")
            print("Exiting.")
            sys.exit(1)
        gpt.add_to_conversation(Role.ASSISTANT, response.to_json())
        if response.command is not None:
            user_prompt = do_command(response)
            continue
        if response.content:
            user_prompt = do_content_prompt()


def review_command(command: str) -> str:
    """Review the command returned by GPT-4 for safety."""
    command = " ".join(command.strip().split())
    if any([string in command for string in UNSAFE_STRINGS]):
        # The stream handler will have printed the error message in the
        # contents.
        print("Unsafe command. Exiting.")
        sys.exit(1)
    return command


def check_input(match: re.Match) -> str:
    """Check the input of the user for root directory operations."""
    user_input = input(f"Enter the value for {match.group(0)}: ")
    if user_input == "/" or user_input == "/*":
        print(f"Unsafe input {user_input}. Exiting.")
        sys.exit(1)
    return user_input


def process_command(command: str) -> str:
    """Process the command returned by GPT-4.

    Ask the user for input for each placeholder surrounded by angle brackets.
    """
    pattern = r"<([^<>]+)>"
    # Simple, non-matching count of angle brackets.
    if len(re.findall(r"<", command)) != len(re.findall(r">", command)):
        raise ValueError("Mismatched angle brackets")
    return re.sub(pattern, check_input, command)


def main() -> None:
    """Main entry point for Calais."""
    os_name = platform.system()
    system_prompt = COMMAND_SYSTEM_PROMPT + f"\n The OS is {os_name}."
    gpt = initialize_gpt(system_prompt)
    user_prompt = " ".join(sys.argv[1:])
    if user_prompt == "":
        user_prompt = input("> Prompt: ")
    try:
        converse(gpt, user_prompt)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
