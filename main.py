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

import chat
import client
from system_prompt import COMMAND_SYSTEM_PROMPT

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


def initialize_gpt(system_prompt: str) -> chat.Chat:
    """
    Initialize the GPT-4 model by checking for the API key, creating a chat
    object, and setting the system prompt.
    """
    if "OPENAI_API_KEY" not in os.environ:
        print(
            "Please set the OPENAI_API_KEY environment variable to your OpenAI API key."
        )
        sys.exit(1)
    chat_client = client.OpenAIClient(
        os.environ["OPENAI_API_KEY"],
        MODEL,
        MAX_TOKENS,
        TEMPERATURE,
    )
    gpt = chat.Chat(
        chat_client,
        MAX_RETRIES,
        TIMEOUT,
        RETRY_DELAY,
        MAX_EMPTY_CHUNKS,
    )
    gpt.add_to_conversation("system", system_prompt)
    return gpt


def chat_with(gpt: chat.Chat, user_prompt: str) -> NoReturn:
    """Chat with GPT-4, looping until the user decides to stop."""
    while True:
        gpt.add_to_conversation("user", user_prompt)
        response = gpt.call_gpt4(user_prompt, True)
        gpt.add_to_conversation("assistant", response)
        user_prompt = input("\n> Prompt ([q] to quit): ")
        if user_prompt.lower() in ["", "q", "quit", "exit"]:
            sys.exit(0)


def review_command(command: str) -> str:
    """Review the command returned by GPT-4 for safety."""
    command = " ".join(command.strip().split())
    if any([string in command for string in UNSAFE_STRINGS]):
        print(f"Unsafe command {command}. Exiting.")
        sys.exit(1)
    return command


def create_command(gpt: chat.Chat, user_prompt: str) -> NoReturn:
    """
    Create a command from the user prompt and run it in the shell.
    """
    command = gpt.call_gpt4(user_prompt, False)
    command = process_command(command)
    command = review_command(command)
    while True:
        run_command = input(f"Run [Y/n/(e)xplain] `{command}`: ")

        match run_command.lower():
            case "" | "y" | "yes":
                try:
                    subprocess.run(command, shell=True, check=True)
                except KeyboardInterrupt:
                    print("Execution interrupted by user. Exiting.")
                finally:
                    sys.exit(0)

            case "c" | "ch" | "chat":
                pass
            case "n" | "no" | "q" | "quit" | "exit":
                sys.exit(0)
            case "e" | "ex" | "explain":
                user_prompt = f"Explain the command `{command}`"
                gpt.call_gpt4(user_prompt, True)
                print("")


def check_input(match: re.Match) -> str:
    """
    Check the input of the user to make sure they're not operating on the root
    directory.
    """
    user_input = input(f"Enter the value for {match.group(0)}: ")
    if user_input == "/" or user_input == "/*":
        print(f"Unsafe input {user_input}. Exiting.")
        sys.exit(1)
    return user_input


def process_command(command: str) -> str:
    """
    Process the command returned by GPT-4, asking the user for input for each
    placeholder surrounded by angle brackets.
    """
    if command == "unsafe command":
        print("GPT-4 thinks this would be an unsafe command. Exiting.")
        sys.exit(1)
    pattern = r"<([^<>]+)>"
    # Simple, non-matching count of angle brackets.
    if len(re.findall(r"<", command)) != len(re.findall(r">", command)):
        raise ValueError("Mismatched angle brackets")
    print(f"The command is: `{command}`")
    return re.sub(pattern, check_input, command)


def main() -> None:
    """
    Main entry point for calais. If the first argument is `-c`, chat with
    GPT-4. Otherwise, create and run a command.
    """
    if len(sys.argv) < 2:
        print("Usage: main.py <user_prompt>     # Create and run a command")
        print("Usage: main.py -c <user_prompt>  # Chat")
        sys.exit(1)

    try:
        match sys.argv[1]:
            case "-c":
                gpt = initialize_gpt("")
                user_prompt = " ".join(sys.argv[2:])
                chat_with(gpt, user_prompt)
            case _:
                os_name = platform.system()
                system_prompt = COMMAND_SYSTEM_PROMPT + f"\n The OS is {os_name}."
                gpt = initialize_gpt(system_prompt)
                user_prompt = " ".join(sys.argv[1:])
                create_command(gpt, user_prompt)
    except chat.ChatError as e:
        print(f"Unrecoverable error: '{e}'. Exiting.")


if __name__ == "__main__":
    main()
