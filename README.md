
# Calais

### Command Line AI for fast, easy commands.

Calais speeds your interaction in terminal shells. It writes commands by sending
your requests to `GPT-4` to be turned into commands that you can run. So
 * You write natural language requests instead of commands.
 * You don't have to remember which commands to use.
 * You don't have to remember command line syntax. 
 * You can execute as fast as you can type what you want.
 * You can learn Linux shell commands by watching best-practice examples.

### Features
 * For safety, it shows you the command before running it so you can confirm it.
   [Always review the command before running it. See 
   [Safeties and Cautions](#safeties-and-cautions).]
 * You can ask it to explain the command it returns.
 * It will ask for needed parameters.
 * You can have longer chats with GPT-4 instead of just generating commands.
 * The command is `ai` for simplicity and speed.
 * It assumes common command line utilities so casual language will usually
   return the right result.


### Examples

```bash
$ ai list uncommitted files
The command is: `git status --short`
Run [Y/n/(e)xplain] `git status --short`:      # <-- [Hit enter]
M  main.py
A  pyproject.toml
D  setup.py
?? LICENSE
?? README.md
?? dist/
```
Not that you didn't have to even specify `git`. It assumes common utilities so
you can use casual language and GPT-4 understands what you intend. You can
specify what you need if necessary.

It provides a speedup over looking up arcane command syntax:

```bash
$ ai update current commit without writing
The command is: `git commit --amend --no-edit`
Run [Y/n/(e)xplain] `git commit --amend --no-edit`:
```

The commands can be as sophisticated as you can describe and GPT-4 can generate:

```bash
$ ai list homedir python files by size then search the top 3 for the word group
The command is: `ls -lSr ~/*.py | head -3 | awk '{print $9}' | xargs grep -l 'group'`
Run [Y/n/(e)xplain] `ls -lSr ~/*.py | head -3 | awk '{print $9}' | xargs grep -l 'group'`:      # <-- [Hit enter]
ai_critics_analysis.py
```

I even find that it's faster to use Calais for simple commands that I already
know because I don't have to type the correct syntax.

```bash
$ ai echo path
The command is: `echo $PATH`
Run [Y/n/(e)xplain] `echo $PATH`:      # <-- [Hit enter]
/opt/homebrew/Cellar/pyenv/2.3.36/plugins/python-build/bin:/usr/local/Caskroom/...
```
### Argument Request

If you ask for a command that needs more information, `Calais` will ask for it
and use it to complete the command:

```bash
$ ai add and commit files
The command is: `git add . && git commit -m "<message>"`
Enter the value for <message>: added license and README.py
Run [Y/n/(e)xplain] `git add . && git commit -m "added license and README.py"`:
[main 757b988] added license and README.py
 3 files changed, 368 insertions(+)
 create mode 100644 LICENSE
 create mode 100644 README.md
```


### Explain

You can ask Calais to explain the command it generated:

```bash
$ ai show files by size largest last
The command is: `ls -lrS`
Run [Y/n/(e)xplain] `ls -lrS`: e
The `ls -lrS` command in Unix is used to list files and directories.

- The `-l` option stands for "long format", which includes additional 
information such as the file permissions, number of links, owner, group, size, 
and time of last modification.
- The `-r` option stands for "reverse", which reverses the order of the sort to 
get reverse lexicographical order or the oldest entries first (or largest files 
last when used with -S).
- The `-S` option stands for "size", which sorts files by size.

So, `ls -lrS` will list all files and directories in the current directory in 
long format, sorted by size in reverse order (largest last).
Run [Y/n/(e)xplain] `ls -lrS`:
```


## Chat mode
You can also use `Calais` to chat with GPT-4 using `-c`. 

```text
$ ai -c write out the first 4 lines of the canterbury tales
Whan that Aprill with his shoures soote
The droghte of March hath perced to the roote,
And bathed every veyne in swich licour
Of which vertu engendred is the flour;
> Prompt ([q] to quit): 4 more
Whan Zephirus eek with his sweete breeth
Inspired hath in every holt and heeth
The tendre croppes, and the yonge sonne
Hath in the Ram his halfe cours yronne;
> Prompt ([q] to quit): q
```

## Requirements
`Calais` requires an OpenAI API key that can run `GPT-4`. 
## Installation

Install the Python package using Pip:
```bash
$ pip install calais
```

`Calais` will need your OpenAI API key exported as an environment variable:

```bash
$ export OPENAI_API_KEY='sk-your-open-ai-key'
```

### Shell interpolation

Note that on the command line, you can't use punctuation that would be
interpreted by the shell like apostrophes or question marks. If you want to use
this punctuation, enclose the string in quotes.

```text
$ ai what's the OS version
quote> ^C                      # It's continuing the quote started in "what's"
$ ai "what's the OS version?"
The command is: `sw_vers -productVersion`
Run [Y/n/(e)xplain] `sw_vers -productVersion`:
14.2.1
```


## Limitations

1. Although it uses a system prompt that instructs it to generate runnable
commands, `GPT-4` sometimes returns elaborate text explanations or scripts:

```text
$ ai automatically watch files for changes and turn unit tests, sending an email
if they fail The command is: `This task requires a combination of several tools 
and scripting. Here's a basic outline of how you might set this up:

1. Use a tool like `inotifywait` (or `fswatch` on MacOS) to watch for file 
changes.
2. When a change is detected, run your unit tests using whatever tool is 
appropriate for your project.
3. If the tests fail, send an email using a tool like `mail`.

Here's an example of how you might set this up in a bash script:

#!/bin/bash

while true; do
  fswatch -o <directory_to_watch> | while read f; do
    make test || echo "Tests failed" | mail -s "Test Failure" <email>
  done
done

Replace `<directory_to_watch>` with the directory you want to watch for changes,
`<email>` with the email address you want to send notifications to, and `make 
test` with the command to run your tests.

Please note that this is a very basic example and may not work perfectly for
your needs. You'll likely need to customize it to fit your specific project and 
environment.`
Enter the value for <directory_to_watch>: `
```

2. GPT-4, like all current Large Language Models may hallucinate or make other
   errors. Always review the returned command before running it.

## Safeties and Cautions

This program presents commands generated by GPT-4 for you to run. Unsafe
commands could be generated. Unsafe commands are those that could delete data,
cause your system to become unresponsive, or cause other problems. __Always review
the commands before running them.__

Two safety mechanisms are included:
1. GPT-4 is instructed not to return unsafe commands.
2. The program does simple checks for unsafe commands and inputs.

```text
$ ai erase the disk
GPT-4 thinks this would be an unsafe command. Exiting.
```

Unsafe commands could slip past these checks. These checks cannot prevent all
potentially unsafe commands from being generated or run. Do not use this program
on systems with sensitive or valuable data. Use at your own risk.

The primary risk mitigation is that commands are shown to you for confirmation
before they are run. Always review the commands before running them. 

Note that these simple safety checks my prevent the programs from generating 
commands that are actually safe to run.