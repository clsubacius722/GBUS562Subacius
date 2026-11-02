## What I Built

I built the Prompt Lab, a single-page web app (`prompt-lab.html`) that sends prompts to Claude (`claude-sonnet-5`) through the Anthropic API, with an optional system prompt and the whole conversation kept as context. A small launcher (`start-prompt-lab.bat`) serves the page on my computer so that the Export button can save each conversation as a Markdown file in `Assignment-Week02/runs`, with the model name on the first line, a speaker heading on every message, and any API key removed. For the four runs, the system prompt was a Brand Kit for Wildframe Coffee Roasters, a fictional specialty coffee roaster: its brand voice, its customers, one house bean card and two past customer replies. Each run then gave Claude one task: subscriber perks (`task-01.md`), bean cards (`task-02.md`), customer replies (`task-03.md`) and choosing a pop-up location (`task-04.md`).

## Why This Approach

Task 1 - Technique: zero-shot
Task 1 asks for six new perk ideas for subscribers who stay six months or longer, which is open-ended brainstorming with no single right answer. Example perks would have anchored Claude on those ideas and narrowed the range, so the prompt gives no example perks and instead sets the form directly: six ideas, a numbered list, one sentence each, no more than 25 words. The brand voice and eco-conscious customers in the Brand Kit supply the tone, so the task needs clear constraints rather than demonstrations.

Task 2 - Technique: one-shot
Task 2 is a formatting task: three new coffees each need a bean card with the same labels in the same order as the house format. The Brand Kit contains exactly one bean card (Huila, Colombia), and one example is enough to pin down a fixed five-line template; zero-shot would leave Claude guessing the labels, and more cards would add length without adding information. The task supplies all the facts (origin, roast, notes, brew method), so the only creative part is the "Real talk" line, where the single example also shows the expected tone.

Task 3 - Technique: few-shot
Task 3 asks for replies to three customer comments in Wildframe's voice, and a voice is easier to show than to describe: "warm, plainspoken, and a little irreverent" leaves a lot of room for interpretation. The two past comment-and-reply pairs show how Wildframe actually answers, owning a problem and offering a fix (the burnt Kenya roast) and answering a pointed question honestly with a light touch (the packaging), which maps directly onto the late-order complaint and the decaf question in this task. Those examples are also about 25 words each, which steers Claude toward short replies that fit the 40-word limit.

Task 4 - Technique: zero-shot
Task 4 asks Claude to choose one location for a four-week pop-up with a $5,000 rent budget and to end with a single "Recommendation:" line. It is a decision with one answer rather than a style to imitate, so examples of other recommendations would not help, and the prompt gives none; the required final line sets the form. The weakness is that the task depends on location data (rents, foot traffic, audience) that was not in the prompt, which a zero-shot prompt cannot make up for; I discuss this in the Reflection.

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

Customer replies. Reply to these three customer comments in Wildframe's voice. Required format: three replies numbered 1 to 3, each no more than 40 words, with no emoji.
1. My order was supposed to arrive Monday. It's Thursday.
2. Do you make any decaf that doesn't taste like cardboard?
3. The Huila is my new Sunday morning ritual. Thank you.

### Claude

1. That's on us, not the mail carrier's. Four days late isn't "Monday-ish." Send us your order number and we'll fix it fast, no excuses.

2. We do, and it actually tastes like coffee. Our Swiss Water decaf keeps the flavor, loses the caffeine and the cardboard vibes.

3. That makes our whole week. Huila's got a way of turning Sundays into something worth looking forward to. Enjoy every cup.

## Reflection

The one-shot bean card in Task 2 made the biggest difference. Claude reproduced the house format exactly: all three cards use the same five labels in the same order, origins are in capitals like the Huila example, and each "Real talk" line matches the example's dry humor. Without that card, Claude would have had to invent the labels. One side effect was that Claude wrapped the cards in a code block under a "# Task 2" heading, because my prompt included a stray note about naming the export file, which shows that Claude treats every line of a prompt as part of the task. The few-shot replies in Task 3 also landed the voice: each reply owns the problem or the compliment in under 40 words with no emoji, much like the two examples. But reply 2 promises a "Swiss Water decaf" that appears nowhere in the Brand Kit, so examples teach tone, not facts, and a real reply would need a product list. Task 1's zero-shot perks met every rule and sounded on-brand, which suggests the voice description alone was enough for brainstorming. The choice I am least sure of is Task 4. Claude did not guess: it said the location data was missing, asked for it, and ended with "Recommendation: Pending location data", which follows the format but names no location. Next time I would use chain-of-thought instead: paste the location table into the prompt and ask Claude to work through each option step by step (four-week rent against the $5,000 budget, then foot traffic and customer fit) before the Recommendation line.
