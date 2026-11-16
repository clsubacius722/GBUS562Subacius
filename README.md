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

4. week-04: [HR email agent](week-04/)

   Week 4: an AI agent that prepares replies to HR emails using tools from an MCP server, built with Claude Code. I first built it for the lecture's Hartwell Foods files ([hartwell-hr](week-04/hartwell-hr/)), then pointed it at Ridgeline Hotels ([ridgeline-hotels](week-04/ridgeline-hotels/)). The [runs](week-04/runs/) folder holds the seven saved Ridgeline runs, and my [writeup](week-04/writeup.md) explains what the runs showed.

   **The code** has two Python files:

   - [hr_mcp_server.py](week-04/hr_mcp_server.py) is an MCP server with two tools. `search_policy` searches the organization's HR documents (stored in a Chroma database, one chunk per section) and returns the 4 closest sections with their source file, so every policy fact can be cited. `get_leave_balance` reads the employee file. The server never calls Claude and needs no API key.
   - [agent.py](week-04/agent.py) reads one email, starts the server, and runs Claude's tool-use loop (`claude-sonnet-5`). It adds a third tool, `save_reply`, which only saves a draft for a person to review and never sends anything. It stops after 10 tool calls at most, and prints every step, then a `DRAFT` line, the reply, and `Needs human review: true` or `false`.
   - Options: `--org` picks the organization folder (default `hartwell-hr`), and `--save` writes everything printed to a text file. Each organization gets its own Chroma database, kept out of Git. The server doesn't assume the employee file's column names; it works out the email and balance columns from the header row, which is why Ridgeline's differently laid-out file works without changes.

   **How the code keeps balances private:** `agent.py` takes the sender's address from the email's From: line and starts the server locked to that one person (`--as-employee`). In that mode `get_leave_balance` takes no inputs, so Claude can only ever get the sender's own balance. When Email 5 hid an "ADMIN OVERRIDE" asking for every team member's balance, Claude refused, and even if it had obeyed, the code gave it no way to look anyone else up. If the sender isn't in the employee file (Email 7), the tool returns an error instead of a number.

   Run it from the repository folder, for example: `.venv/Scripts/python.exe week-04/agent.py --org week-04/ridgeline-hotels --email week-04/ridgeline-hotels/sample-emails/01-jenna-pto.eml --save week-04/runs/ridgeline-01.txt`
