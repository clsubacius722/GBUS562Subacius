# Week 02

2. week-02: [Prompt Lab](prompt-lab.html)

   A web app for testing prompts against Claude (`claude-sonnet-5`) through the Anthropic API, built with Claude Code. This folder holds the Prompt Lab, its launcher, four prompt-engineering runs for Wildframe Coffee Roasters (a fictional specialty coffee roaster), and my [writeup](writeup.md).

## Prompt Lab

A single-page web app for writing prompts and sending them to Claude. Double-click `start-prompt-lab.bat` to open it, paste your Anthropic API key into the API key field (it is never saved), add an optional system prompt, and send prompts. The whole conversation is sent with each new prompt.

- **New Conversation** clears the log and starts over.
- **Export** saves the conversation as a Markdown file in `runs`. The file's first line is the model name, and each message starts with a line naming the speaker: `### System`, `### Cheryl Subacius` or `### Claude`. Any API key is removed before the file is saved.

## Runs

The four exported runs, one per task, in [runs](runs/):

1. [task-1.md](runs/task-1.md): Subscriber perks, six perk ideas for subscribers who stay six months or longer
2. [task-2.md](runs/task-2.md): Bean cards for three new coffees in the house format
3. [task-3.md](runs/task-3.md): Replies to three customer comments in Wildframe's voice
4. [task-4.md](runs/task-4.md): Choosing a location for a four-week pop-up stand

## Files

- [prompt-lab.html](prompt-lab.html): the Prompt Lab app
- [start-prompt-lab.bat](start-prompt-lab.bat) and [start-prompt-lab.ps1](start-prompt-lab.ps1): the launcher that serves the Prompt Lab at `http://localhost:8562` and saves exports
- [writeup.md](writeup.md): what I built, why each prompting technique fits its task, an example run, and a reflection
- [brand-brief.md](brand-brief.md): the brand brief from the course examples
- [runs](runs/): the exported runs
