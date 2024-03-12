
# Calais

### Command Line AI for fast, easy commands.

`Calais` speeds your interaction in terminal shells by commands for you using
`GPT-4`. So
 * You write natural language requests instead of commands.
 * You don't have to remember which commands to use.
 * You don't have to remember command syntax. 
 * You can execute almost as fast as you can type what you want.
 * You can learn Linux shell commands by watching best-practice examples.

### Features
 * For safety, it shows you the command before running it so you can confirm it.
   [Always review the command before running it. See 
   [Safeties and Cautions](#safeties-and-cautions).]
 * You can ask it to explain the command it returns.
 * It will ask for needed parameters.
 * You can chat with GPT-4 in addition to generating commands.
 * The command is `ai` for simplicity and speed.
 * It assumes common command line utilities so casual language will usually
   return the right result.


### Examples

```
$ ai list uncommitted files
Command: `git status --porcelain`
[r]un,(e)xplain],(q)uit, or continue chatting:             # <-- [Hit enter]
 M README.md
MM chat.py
MM client.py
AM content_printer.py
...
```
Note that you didn't have to even specify `git`. It assumes common utilities so
you can use casual language and GPT-4 understands what you intend. You can
specify what you need if necessary.

It provides a speedup over looking up arcane command syntax:

```
$ ai update current commit without writing
Command: `git commit --amend --no-edit`
[r]un,(e)xplain],(q)uit, or continue chatting:             # <-- [Hit enter]
```

The commands can be as sophisticated as you can describe and GPT-4 can generate:

```
$ ai list Python files by size then search the top 3 for the word api
Command: `find . -name '*.py' -exec ls -lS {} + | head -3 | awk '{print $9}' | xargs grep -l 'api'`
[r]un,(e)xplain],(q)uit, or continue chatting:             # <-- [Hit enter]
./tests/test_chat.py
./chat.py
```

I even find that it's faster to use `Calais` for simple commands that I already
know because it's faster to type without correct syntax.

```
$ ai echo path
The command is: `echo $PATH`
Run [Y/n/(e)xplain] `echo $PATH`:      # <-- [Hit enter]
/opt/homebrew/Cellar/pyenv/2.3.36/plugins/python-build/bin:/usr/local/Caskroom/...
```
### Argument Request

If you ask for a command that needs more information, `Calais` will ask for it
and use it to complete the command:

```
$ ai add and commit files
Enter the value for <message>: added JSON response parsing from OpenAI API
Command: `git add . && git commit -m 'added JSON response parsing from OpenAI API'`
[r]un,(e)xplain],(q)uit, or continue chatting:
```


### Explain

You can ask `Calais` to explain the command it generated:

```
$ ai list Python files by size then search the top 3 for the word api
Command: `find . -name '*.py' -exec ls -lS {} + | head -n 3 | awk '{print $9}' | xargs grep -l 'api'`
[r]un,(e)xplain],(q)uit, or continue chatting: e
This command performs several actions in sequence to find Python files
containing the word 'api'. Here's a breakdown: 1. `find . -name '*.py'` searches
the current directory and subdirectories for files ending in '.py'. 2. `-exec ls
-lS {} +` executes `ls -lS` on the found files, listing them in long format
sorted by size in descending order. 3. `head -n 3` takes the top 3 of these
files (the largest ones). 4. `awk '{print $9}'` extracts the 9th field from the
output, which corresponds to the filenames. 5. `xargs grep -l 'api'` uses `grep
-l` to search for the word 'api' in these files, listing only the filenames that
contain the match.
Command: `find . -name '*.py' -exec ls -lS {} + | head -n 3 | awk '{print $9}' | xargs grep -l 'api'`
[r]un,(e)xplain],(q)uit, or continue chatting:
```


## Chatting with GPT-4
You can also use `Calais` to chat with GPT-4:

Here, we ask for some Old English then ask for a translation:

```text
$ ai write out the first 4 lines of the canterbury tales
Whan that Aprille with his shoures soote,
The droghte of March hath perced to the roote,
And bathed every veyne in swich licour
Of which vertu engendred is the flour;
[q]uit, or continue chatting: translate
When April with its sweet-smelling showers
Has pierced the drought of March to the root,
And bathed every vein (of the plants) in such liquid
By which strength the flower is created;
[q]uit, or continue chatting:
```

## Requirements
`Calais` requires an OpenAI API key that can run `GPT-4`. 

## Installation

Install the Python package using Pip:
```bash
$ pip install pycalais
```

`Calais` will need your OpenAI API key exported as an environment variable:

```bash
$ export OPENAI_API_KEY='sk-your-open-ai-key'
```


## Limitations

1. Shell interpolation

Note that on the command line, you can't use punctuation that would be
interpreted by the shell like apostrophes or question marks. If you want to use
this punctuation, enclose the string in quotes.

```text
$ ai what's the OS version
quote> ^C                      # It's continuing the quote started in "what's"
$ ai "what's the OS version?"  # Surrounding the prompt with quotes works...
Command: `sw_vers -productVersion`
[r]un,(e)xplain],(q)uit, or continue chatting:
14.2.1
```

Or just skip the punctuation. GPT-4 will likely understand.

```
$ ai whats the OS version
Command: `sw_vers -productVersion`
[r]un,(e)xplain],(q)uit, or continue chatting:
14.2.1
```

2. Complex Scripts
  
Although it uses a system prompt that instructs it to prefer generate runnable
commands, `GPT-4` sometimes returns scripts:


```text
$ ai automatically watch files for changes and turn unit tests, sending an email if they fail
To automatically watch files for changes, run unit tests, and send an email if
they fail, you can use a combination of shell scripting and tools like
`inotifywait` (for Linux) or `fswatch` (for macOS), along with your testing
framework and a command-line email tool like `sendmail` or `mail`. Since the OS
is Darwin, we'll use `fswatch`. This script is a basic example and might need
adjustments based on your specific testing framework and email setup:

#!/bin/bash

DIRECTORY_TO_WATCH='./your_project_directory'
TEST_COMMAND='your_test_command' # Replace with your specific test command
EMAIL='your_email@example.com'

fswatch -o $DIRECTORY_TO_WATCH | while read change; do
  $TEST_COMMAND
  if [ $? -ne 0 ]; then
    echo 'Tests failed, sending email.'
    echo 'Unit tests failed at $(date)' | mail -s 'Unit Test Failure' $EMAIL
  fi
done

1. Replace `./your_project_directory` with the path to the directory containing
   the files you want to watch.
2. Replace `your_test_command` with the command you use to run your unit tests.
3. Replace `your_email@example.com` with your email address.

Make sure you have `fswatch` installed (`brew install fswatch` if you're using
Homebrew). Also, ensure you have a mail server configured for sending emails
from the command line, or use a command-line email tool that supports your
email provider.
[q]uit, or continue chatting:
```

`Calais` does not try to save or run these scripts. You can copy these from the
output to run them.

3. GPT-4, like all current Large Language Models may hallucinate or make other
   errors. 
   
   Always review the returned command before running it.

## Safeties and Cautions

This program presents commands generated by GPT-4 for you to run. Unsafe
commands could be generated. Unsafe commands are those that could delete data,
cause your system to become unresponsive, or cause other problems. __Always review
the commands before running them.__

Two safety mechanisms are included:
1. GPT-4 is instructed not to return unsafe commands.
2. The program does simple checks for unsafe commands and inputs.

```
$ ai erase the disk
GPT-4 returned an error:
[unsafe command requested]
Exiting.
```

Unsafe commands could slip past these checks. These checks cannot prevent all
potentially unsafe commands from being generated or run. Do not use this program
on systems with sensitive or valuable data. Use at your own risk.

The primary risk mitigation is that commands are shown to you for confirmation
before they are run. Always review the commands before running them. 

Note that these simple safety checks may prevent the programs from generating 
commands that are actually safe to run.

## Code 

The code demonstrates the following features in working with the OpenAI API:
- Streaming Chat Completions so that the text is returned to the user as it is generated. 
- JSON output so that GPT-4 returns structured output.
- Streaming JSON extraction so that the user sees clean generated text, even though the text is embedded within JSON structures that have not yet completed.
- Retry and error handling so that network or other intermittent errors do not prevent a successful API call.

