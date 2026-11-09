# GBUS562Subacius
Repository for Fall 2026 GBUS562

This repository contains my weekly assignments for GBUS562 at the University of Mary Washington (UMW).

## Weekly Work

1. week-01: [Connect 4](week-01/connect4.html)

   A single-page Connect 4 game built with HTML, CSS and JavaScript. Play against a computer opponent that looks ahead several moves (Easy, Medium or Hard), or switch to two-player mode and take turns with a friend on the same device. Open the file in any web browser to play.

2. week-02: [Prompt Lab](week-02/prompt-lab.html)

   A web app for testing prompts against Claude (`claude-sonnet-5`) through the Anthropic API, built with Claude Code. The [week-02 folder](week-02/) holds the Prompt Lab, its launcher (`start-prompt-lab.bat`, which saves each exported conversation as a Markdown file), four prompt-engineering runs for Wildframe Coffee Roasters in [runs](week-02/runs/) (zero-shot, one-shot, few-shot and chain-of-thought), and my [writeup](week-02/writeup.md). See the [week-02 README](week-02/README.md) for details.

3. week-03: [RAG tool (ask.py)](week-03/ask.py)

   Week 3: a RAG tool that answers questions from Copperline Manufacturing's finance documents, built with Claude Code. `ask.py` splits documents into one chunk per section, stores them in a Chroma database, retrieves the 4 most relevant chunks, and has Claude (`claude-sonnet-5`) answer only from them, citing each source file. A `--docs` option points it at any document folder, which I used for Larkfield Credit Union's documents ([larkfield-docs](week-03/larkfield-docs/)), where I found and archived an outdated fee schedule ([larkfield-archive](week-03/larkfield-archive/)). The [runs](week-03/runs/) folder holds the seven saved runs (Question 1 before and after the fix, and Questions 2 to 6), and my [writeup](week-03/writeup.md) explains the chunking and the fix. The Copperline documents are in [copperline-docs](week-03/copperline-docs/).
