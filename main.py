#!/usr/bin/env python3

import platform
import subprocess
import sys

from halo import Halo

import chat

MAX_RETRIES = 3
RETRY_DELAY = 5  # Seconds
MAX_EMPTY_CHUNKS = 10
TIMEOUT = 60  # Seconds

SYSTEM_PROMPT = """
You are an expert command-line interface (CLI) assistant. 

Translate the following user prompt into precise command line commands that can be executed directly
in a Unix-based shell. Focus on selecting the most appropriate utility and flags for each task.
Example requests and their translations are provided for guidance:

- Example request: 'list all directories in the current directory'
- Command: 'ls -d */'

- Example request: 'find all text files in a directory'
- Command: 'find . -type f -name "*.txt"'

- Example request: 'list files that are executable'
- Command: 'find . -type f -executable'

If the response command requires arguments to be given by the user, return the command with a
placeholder. 

- Example request: 'search for a file'
- Command: 'find . -name <filename>'

- Example request: 'search for a file with a specific name in a specific directory'
- Command: 'find <directory> -name <filename>'

The user may assume common utilities are available, such as 'git' and make requests relevant to
them.

- Example request: 'commit'
- Command: 'git commit -m "<message>"'

Return just the command without labels or quotes.
"""

def initialize_gpt():
    gpt = chat.Chat(MAX_RETRIES, TIMEOUT, MAX_EMPTY_CHUNKS, RETRY_DELAY)
    os_name = platform.system()
    system_prompt = SYSTEM_PROMPT + f" The OS is {os_name}."
    gpt.set_system_prompt(system_prompt)
    return gpt

def talk_to(gpt, user_prompt):
    spinner = Halo(text='Loading', spinner='dots')
    spinner.start()
    command = gpt.call_gpt4(user_prompt)
    spinner.stop()
    spinner.clear()
    return command

# Process, the command, asking the user for input for each placeholder surrounded by angle brackets.
def process_command(command):
    command = command.strip()
    while "<" in command:
        placeholder = command.split("<")[1].split(">")[0]
        user_input = input(f"Enter the value for <{placeholder}>: ")
        command = command.replace(f"<{placeholder}>", user_input, 1)
    return command


def main():
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        print("Usage: main.py <user_prompt>")
        sys.exit(1)

    gpt = initialize_gpt()
    while True:
        command = talk_to(gpt, user_prompt)
        print(f"Command: `{command}`")
        command = process_command(command)
        print(f"Command: `{command}`")
        run_command = input(f"Run `{command}` [Y/n/(a)dd? ")

        match run_command.lower():
            case '' | 'y' | 'yes':
                process = subprocess.Popen(command, shell=True)
                process.wait()
                sys.exit(0)
            case 'a' | 'add':
                user_prompt += input("Add to prompt: ")
            case 'n' | 'no':
                sys.exit(0)
    
if __name__ == "__main__":
    main()
