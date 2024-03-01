
# Calais

### Command Line AI for fast, easy commands.

Calais speeds your interaction in terminal shells. It writes commands by sending your requests to `GPT-4` to be turned into commands that you can run. So
 * You write natural language requests instead of commands.
 * You don't have to remember which commands to use.
 * You don't have to remember command line syntax. 
 * You can execute as fast as you can type what you want.
 * You can learn Linux shell commands by watching best-practice examples.

For safety, it shows you the command before running it so you can confirm it.

### Examples
The command is run as `ai` for simplicity and speed.

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
Not that you didn't have to even specify `git`. It assumes common utilities and you can specify what you need if necessary. But you can use casual language and GPT-4 understands what you intend.

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

I even find that it's faster to use Calais for simple commands that I already know because I don't have to type the correct syntax.

```bash
$ ai echo path
The command is: `echo $PATH`
Run [Y/n/(e)xplain] `echo $PATH`:      # <-- [Hit enter]
/opt/homebrew/Cellar/pyenv/2.3.36/plugins/python-build/bin:/usr/local/Caskroom/...
```
### Argument Request

If you ask for a command that needs more information, `Calais` will ask for it and use it to complete the command:

```bash

```

### Explain

You can ask Calais to explain the command it generated:

```bash
$ ai list uncommitted files
The command is: `git status --porcelain`
Run [Y/n/(e)xplain] `git status --porcelain`:      # <-- [Hit e, then enter]
The `git status --porcelain` command shows the status of the working directory and the staging area in a short, easy-to-parse format. This is useful for scripts and other tools that need to understand the status of a Git repository. The `--porcelain` option ensures the output format remains consistent across different versions of Git.
Run [Y/n/(e)xplain] `git status --porcelain`:
 M main.py
?? LICENSE
?? README.md
?? dist/
```

Note that GPT-4 returned a different command than the same request above. 

## Chat mode
You can also use `Calais` to chat with GPT-4 using `-c`. 

```bash
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

### Shell interpolation

Note that on the command line, you can't use punctuation that would be interpreted by the shell like apotrophes or question marks. If you want to
use this punctuation, enclose the string in quotes.

```bash
$ ai what's the OS version
quote> ^C
$ ai "what's the OS version"
The command is: `sw_vers -productVersion`
Run [Y/n/(e)xplain] `sw_vers -productVersion`:
14.2.1
```


## Limitations

Although it uses a system prompt to instruct it to generate runnabld commands, `GPT-4` sometimes returns elaborate scripts:

```bash
$ ai automatically watch files for changes and turn unit tests, sending an email if they fail
The command is: `This task requires a combination of several tools and scripting. Here's a basic outline of how you might set this up:

1. Use a tool like `inotifywait` (or `fswatch` on MacOS) to watch for file changes.
2. When a change is detected, run your unit tests using whatever tool is appropriate for your project.
3. If the tests fail, send an email using a tool like `mail`.

Here's an example of how you might set this up in a bash script:

```bash
#!/bin/bash

while true; do
  fswatch -o <directory_to_watch> | while read f; do
    make test || echo "Tests failed" | mail -s "Test Failure" <email>
  done
done
```

Replace `<directory_to_watch>` with the directory you want to watch for changes, `<email>` with the email address you want to send notifications to, and `make test` with the command to run your tests.

Please note that this is a very basic example and may not work perfectly for your needs. You'll likely need to customize it to fit your specific project and environment.`
Enter the value for <directory_to_watch>: `
```

`GPT-4` may not correctly report which model it is:

```bash
$ ai -c what model are you
I am an AI model developed by OpenAI, known as GPT-3.
> Prompt ([q] to quit):
```
That's a known issue. You can try it out for yourself by asking the question here after confirming that the selected model is `GPT-4`.
https://platform.openai.com/playground?mode=chat&model=gpt-4