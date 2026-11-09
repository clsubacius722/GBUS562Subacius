## What I Built
I built `ask.py`, a Python command-line tool that answers questions from a folder of documents using retrieval-augmented generation. It splits each document (HTML, PDF, Word, Markdown or plain text) into one chunk per section, stores the chunks in a Chroma database using Chroma's built-in embedding model, retrieves the 4 chunks most similar to the question, and sends them to Claude (`claude-sonnet-5`) with instructions to answer only from those sources, cite the source file for each fact, and say so when the sources don't contain the answer. I first built and tested it on Copperline Manufacturing's finance documents. To make it work with Larkfield's documents, I added a `--docs` option to choose the document folder, kept a separate Chroma database for each folder (rebuilt automatically when files change, all kept out of Git), and added a `--save` option that writes the retrieved chunks, a line containing only ANSWER, and Claude's answer to a text file. I saved seven runs in `runs/`: Question 1 before and after fixing Larkfield's document collection (`q1-before.txt`, `q1-after.txt`) and Questions 2 to 6 (`q2.txt` to `q6.txt`).

## Why This Approach
Chunking method: structure
Makes sense on its own: Yes, because each chunk is a whole section under one heading with a label line on top; for example, the chunk "Consumer Fee Schedule [Version 8 (current). Replaces Version 7] | Wire transfers" lists all four wire fees together, so it can be understood without the rest of the document.
Label and source: Both, because every chunk's text starts with a label line giving the document title, its version line and the section heading, and the source file is stored with each chunk and printed as "source: file-name" for every retrieved chunk in my saved runs.
Short enough: Yes, because I measured every chunk: the largest Larkfield chunk (the overdraft fee section) is 122 words and the largest Copperline chunk is 141 words, and ask.py splits any longer section at paragraph breaks.

## Example Run
Question 4: Can I refund the outgoing international wire transfer fee for a member without approval from a manager?

```
[1] similarity 0.615 | source: consumer-fee-schedule.html
Consumer Fee Schedule [Version 8 (current). Replaces Version 7] | Wire transfers - Incoming domestic wire transfer: $10. - Incoming international wire...

[2] similarity 0.603 | source: fee-refund-guide.html
Fee Refund Guide for Member Service Staff [Version 2 (current)] | Refunds that need a branch manager A refund needs the branch manager's approval when...

[3] similarity 0.570 | source: fee-refund-guide.html
Fee Refund Guide for Member Service Staff [Version 2 (current)] | What a member service representative can approve A member service representative may...

[4] similarity 0.522 | source: fee-refund-guide.html
Fee Refund Guide for Member Service Staff [Version 2 (current)] | Refunds that need the Member Services Director Refunds of more than $150 in total fo...

ANSWER
No. The outgoing international wire transfer fee is **$45** (Source: consumer-fee-schedule.html). A member service representative can only approve refunds of a single fee of **$30 or less** without further approval (Source: fee-refund-guide.html). Since $45 exceeds $30, it requires **branch manager approval** (Source: fee-refund-guide.html).
```

## Reflection
What was wrong: The problem was `consumer-fee-schedule-v7.html`, an outdated Version 7 of the fee schedule that still called itself "Version 7 (current)" even though `consumer-fee-schedule.html` (Version 8) replaced it. The retrieved chunks for Question 1 in `q1-before.txt` showed two chunks from each version: v7's overdraft section ($35 per item, up to four fees a day) ranked second at 0.698, right behind Version 8's overdraft section ($29) at 0.720, so half the retrieved chunks came from an out-of-date document. Claude happened to answer $29 in that run, but only by choosing between two documents that both claimed to be current, so the answer was not reliable: with slightly different wording the $35 chunk could rank first.
How I fixed it: Moved `consumer-fee-schedule-v7.html` out of `week-03/larkfield-docs` into a separate `week-03/larkfield-archive` folder that the tool does not index, then rebuilt the database, which went from 39 chunks from 6 files to 30 chunks from 5 files; in `q1-after.txt` all four retrieved chunks come from `consumer-fee-schedule.html` and the answer gives the current $29 fee.
Prevention: Archive process, so that whenever Member Services publishes a new version of a document, the same person moves the old version out of the shared-drive folder the tool reads into an archive folder that day, marks it as superseded, and rebuilds the database before staff use the tool again.
Question 6: Declined, because retrieval returned only weakly related chunks with low similarity scores (0.193 to 0.278): fee schedule sections on stop payments, checking account monthly fees and dormant accounts, plus the share certificate dividend rates, none of which mention mortgages, so the tool said Larkfield Credit Union's documents do not contain that information.
