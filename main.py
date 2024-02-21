#!/usr/bin/env python3

import os
import platform
import re
import subprocess
import sys

from halo import Halo

import chat
from system_prompt import COMMAND_SYSTEM_PROMPT

MAX_RETRIES = 3
RETRY_DELAY = 5  # Seconds
MAX_EMPTY_CHUNKS = 20
TIMEOUT = 60  # Seconds

def initialize_gpt(system_prompt):
    """
    Initialize the GPT-4 model.
    """
    gpt = chat.Chat(MAX_RETRIES, TIMEOUT, MAX_EMPTY_CHUNKS, RETRY_DELAY)
    gpt.set_system_prompt(system_prompt)
    return gpt

def talk_to(gpt, user_prompt):
    """
    Send the prompt to  GPT-4 and return the response, using a spinner to indicate that the model is
    working.
    """
    spinner = Halo(text='GPT-4>', spinner='dots')
    spinner.start()
    command = gpt.call_gpt4(user_prompt, spinner)
    spinner.stop()
    spinner.clear()
    return command

def chat_with(gpt, user_prompt):
    """
    Chat with GPT-4, looping until the user decides to stop.
    """
    while True:
        response = talk_to(gpt, user_prompt)
        print(response)
        user_prompt = input("You ([q] to quit): ")
        if user_prompt.lower() in ["", "q", "quit", "exit"]:
            sys.exit(0)

def create_command(gpt, user_prompt):
    """
    Create a command from the user prompt and run it in the shell.
    """
    command = talk_to(gpt, user_prompt)
    command = process_command(command)
    while True:
        run_command = input(f"Run [Y/n/(e)xplain] `{command}` :")

        match run_command.lower():
            case '' | 'y' | 'yes':
                process = subprocess.Popen(command, shell=True)
                process.wait()
                sys.exit(0)
            case 'n' | 'no':
                sys.exit(0)
            case 'e' | 'ex' | 'explain':
                user_prompt = f"Explain the command `{command}`"
                explanation = talk_to(gpt, user_prompt)
                print(explanation)


def process_command(command):
    """
    Process the command returned by GPT-4, asking the user for input for each placeholder surrounded
    by angle brackets.
    """
    pattern = r"<([^<>]+)>" 
    if len(re.findall(r"<", command)) != len(re.findall(r">", command)):
        raise ValueError("Mismatched angle brackets")
    return re.sub(pattern, lambda m: input(f"Enter the value for {m.group(0)}: "), command)


def main():
    if len(sys.argv) < 2:
        print("Usage: main.py <user_prompt>     # Create and run a command")
        print("Usage: main.py -c <user_prompt>  # Chat")
        sys.exit(1)

    match sys.argv[1]:
        case "-c":
            gpt = initialize_gpt("")
            user_prompt = " ".join(sys.argv[2:])
            chat_with(gpt, user_prompt)
        case _:
            os_name = platform.system()
            system_prompt = COMMAND_SYSTEM_PROMPT + f" The OS is {os_name}."
            gpt = initialize_gpt(system_prompt)
            user_prompt = " ".join(sys.argv[1:])
            create_command(gpt, user_prompt)

if __name__ == "__main__":
    main()
