## What I Built

I built the Prompt Lab, a single-page web app (`prompt-lab.html`) that sends prompts to Claude (`claude-sonnet-5`) with an optional system prompt and keeps the whole conversation as context. A small PowerShell launcher (`start-prompt-lab.bat`) serves the page locally so that the Export button can save each conversation as a Markdown file in `runs/` (`task-01.md`, `task-02.md`, ...), with the model name on the first line, a speaker heading on every message, and any API key removed. For the four runs, I gave Claude a system prompt describing Wildframe Coffee Roasters, a fictional specialty coffee roaster: its brand voice, customers, house bean card format and past customer replies. I then gave it one task per run: subscriber perks, bean cards, [Task 3] and [Task 4].

## Why This Approach

Task 1 - Technique: zero-shot
Task 1 asks for six new perk ideas for subscribers who stay six months or longer, which is open-ended brainstorming with no single right answer. Giving example perks would have anchored Claude on those ideas and narrowed the range, so the prompt gives no examples and instead sets the form directly: six ideas, a numbered list, one sentence each, no more than 25 words. The brand voice and the eco-conscious customers in the system prompt supply the tone, so the task itself needs only clear constraints, not demonstrations.

Task 2 - Technique: one-shot
Task 2 is a formatting task: three new coffees each need a bean card with the same labels in the same order as the house format. The system prompt contains exactly one example card (Huila, Colombia), and one example is enough to pin down a fixed five-line template, which is why one-shot fits better than zero-shot (Claude would have to guess the labels) or few-shot (more examples add length without adding information about the format). The task also supplies all the facts (origin, roast, notes, brew method), so the only creative part is the "Real talk" line, where the single example also shows the expected tone.

Task 3 - Technique: [zero-shot / one-shot / few-shot / chain-of-thought]
[TO DO: at least two sentences on why this technique fits Task 3, pointing to specific features of the task.]

Task 4 - Technique: [zero-shot / one-shot / few-shot / chain-of-thought]
[TO DO: at least two sentences on why this technique fits Task 4, pointing to specific features of the task.]

## Example Run

claude-sonnet-5

### System

Company is called "Wildframe Coffee Roasters", a fictional specialty coffee roaster that sells beans online, through a monthly subscription. 

The brand voice is: Warm, plainspoken, and a little irreverent, with no corporate jargon.

The customers are environmentally conscious urban professionals

House bean card (the format every bean card follows):

HUILA, COLOMBIA
Roast: Medium
Tastes like: red apple, brown sugar, cocoa
Brew it: Pour-over or drip
Real talk: The coffee that converted our office's tea drinker. Mostly.

Past customer replies (comments from customers, with the replies Wildframe posted):

Comment: Is your packaging actually recyclable, or is that just marketing?
Reply: Fair question. The bag is compostable, the little valve isn't, so pop the valve off first. We're working on that last bit.

Comment: Your Kenya roast tasted burnt to me.
Reply: That's not the cup we were going for. Tell us how you brewed it and we'll help you dial it in, or swap you to something mellower.

Comment: Best coffee I've had in years!!

### Cheryl Subacius

Task 2 will be the name of this export markdown file.
Bean cards. Wildframe is adding three coffees to its shop, and every coffee gets a bean card in the house format shown in the Brand Kit. Get one card for each coffee below. Required format: three cards in the house format, with the same labels in the same order.
- Yirgacheffe, Ethiopia. Light roast. Notes: jasmine, lemon, bergamot. Best as pour-over.
- Cerrado, Brazil. Medium-dark roast. Notes: peanut, milk chocolate, low acidity. Good for espresso or French press.
- Chiapas, Mexico. Medium roast. Notes: almond, caramel, orange peel. Good for drip or AeroPress.

### Claude

```markdown
# Task 2

YIRGACHEFFE, ETHIOPIA
Roast: Light
Tastes like: jasmine, lemon, bergamot
Brew it: Pour-over
Real talk: This one's basically a cup of flowers and citrus pretending to be coffee. If you like your mornings delicate, start here.

CERRADO, BRAZIL
Roast: Medium-Dark
Tastes like: peanut, milk chocolate, low acidity
Brew it: Espresso or French press
Real talk: Smooth, nutty, no sharp edges. The coffee equivalent of a weighted blanket.

CHIAPAS, MEXICO
Roast: Medium
Tastes like: almond, caramel, orange peel
Brew it: Drip or AeroPress
Real talk: Easygoing and a little citrusy, like a coffee that's also low-key the nicest person at the party.
```

## Reflection

[DRAFT based on Tasks 1 and 2 only; add Tasks 3 and 4 before submitting.]

Across the first two tasks, the one-shot bean card in Task 2 made the clearest difference. Claude reproduced the house format exactly: all three cards use the same five labels in the same order, the origins are in capitals like the Huila example, and each "Real talk" line matches the example's dry, slightly irreverent tone. Without that example, I would expect different label names or extra fields. One side effect was that Claude wrapped the cards in a code block with a "# Task 2" heading, because my prompt included a note about naming the export file, which shows that stray instructions in the prompt get treated as part of the task. It also put "low acidity" under "Tastes like", copying my notes literally rather than separating flavor from body. Task 1's zero-shot prompt also worked well: all six perks are numbered, one sentence and under 25 words, and the system prompt clearly shaped the voice ("roast us a little back") and the eco angle (compostable filters). Comparing it with an earlier Task 1 attempt that had no system prompt, the ideas were similar but more generic, so the context mattered more than the technique there. The choice I am least sure of is zero-shot for Task 1: two or three example perks could have pushed Claude toward perks that cost Wildframe little, and I would try few-shot next to compare. [Add Tasks 3 and 4.]
