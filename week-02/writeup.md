## What I Built

I built the Prompt Lab, a single-page web app (`prompt-lab.html`) that sends prompts to Claude (`claude-sonnet-5`) through the Anthropic API, with an optional system prompt and the whole conversation kept as context. A small launcher (`start-prompt-lab.bat`) serves the page on my computer so that the Export button can save each conversation as a Markdown file in `runs`, with the model name on the first line, a speaker heading on every message, and any API key removed. The four runs use Wildframe Coffee Roasters, a fictional specialty coffee roaster, and each one gives Claude a different amount of the Brand Kit to match the technique: subscriber perks with no examples (`task-1.md`), bean cards with the one house bean card (`task-2.md`), customer replies with past replies as examples (`task-3.md`), and choosing a pop-up location from the location data, reasoned through step by step (`task-4.md`).

## Why This Approach

Task 1 - Technique: zero-shot
Task 1 asks for six new perk ideas for subscribers who stay six months or longer, which is open-ended brainstorming with no single right answer. Example perks would have anchored Claude on those ideas and narrowed the range, so the system prompt gives only the company, brand voice and customers, and the prompt sets the form directly: a numbered list of exactly six ideas, one sentence each, no more than 25 words. Nothing in the task depends on a house format or past wording, so clear constraints are enough without demonstrations.

Task 2 - Technique: one-shot
Task 2 is a formatting task: three new coffees each need a bean card with the same labels in the same order as the house format. One example is enough to pin down a fixed five-line template, and the run shows why it is needed: before I added the Huila bean card, Claude invented its own labels ("Tasting Notes", "Best Brewed", "The Pitch"), and after seeing that single card it used the exact house labels in order. The task supplies all the facts (origin, roast, notes, brew method), so the only creative part is the "Real talk" line, where the one example also shows the expected tone.

Task 3 - Technique: few-shot
Task 3 asks for replies to three customer comments in Wildframe's voice, and a voice is easier to show than to describe: "warm, plainspoken, and a little irreverent" leaves a lot of room for interpretation. The two past comment-and-reply pairs show how Wildframe actually answers, owning a problem and offering a fix (the burnt Kenya roast) and answering a pointed question honestly with a light touch (the packaging), which maps directly onto the late-order complaint and the decaf question in this task. Those examples are about 25 words each, which steers Claude toward short replies that fit the 40-word limit.

Task 4 - Technique: chain-of-thought
Task 4 is a decision with numbers: choose one of three locations for a four-week pop-up within a $5,000 rent budget. Getting it right takes several dependent steps for each location (visitors times the share who buy times the average sale, minus weekly rent, then four weeks of rent against the budget), and a model that jumps straight to an answer could favor Union Station for its 30,000 visitors even though it loses money and its rent alone ($8,000) breaks the budget. The prompt includes all the location data the task needs and asks for step-by-step reasoning, so Claude works out buyers, revenue, profit and the four-week rent for each location before the required "Recommendation:" line, which makes every number visible and checkable.

## Example Run

claude-sonnet-5

### System

Wildframe Coffee Roasters is a fictional specialty coffee roaster that sells beans online and through a monthly subscription. Brand voice: warm, plainspoken, and a little irreverent, with no corporate jargon. Customers: environmentally conscious urban professionals.

### Cheryl Subacius

 Task 2 (one-shot): 
Bean cards. Wildframe is adding three coffees to its shop, and every coffee gets a bean card in the house format shown in the Brand Kit. Get one card for each coffee below. Required format: three cards in the house format, with the same labels in the same order.
- Yirgacheffe, Ethiopia. Light roast. Notes: jasmine, lemon, bergamot. Best as pour-over.
- Cerrado, Brazil. Medium-dark roast. Notes: peanut, milk chocolate, low acidity. Good for espresso or French press.
- Chiapas, Mexico. Medium roast. Notes: almond, caramel, orange peel. Good for drip or AeroPress.

### Claude

A quick note before diving in: no Brand Kit file came through with this task, so I don't have the actual house format to match. Rather than guess and pass it off as "the" format, here's a clean, consistent bean card template inferred from your brand voice (warm, plainspoken, a little irreverent) — flag it for a quick check, and I'll adjust labels/order to match the real Brand Kit once I see it.

---

**CARD 1**

**Name:** Yirgacheffe
**Origin:** Ethiopia
**Roast:** Light
**Tasting Notes:** Jasmine, lemon, bergamot
**Best Brewed:** Pour-over
**The Pitch:** Floral, bright, and a little fancy — this one's basically tea's cooler coffee cousin. Make it slow, drink it slower.

---

**CARD 2**

**Name:** Cerrado
**Origin:** Brazil
**Roast:** Medium-dark
**Tasting Notes:** Peanut, milk chocolate, low acidity
**Best Brewed:** Espresso or French press
**The Pitch:** Smooth, nutty, no sharp edges. The coffee equivalent of a good pair of broken-in boots.

---

**CARD 3**

**Name:** Chiapas
**Origin:** Mexico
**Roast:** Medium
**Tasting Notes:** Almond, caramel, orange peel
**Best Brewed:** Drip or AeroPress
**The Pitch:** Warm and a little citrusy, like your favorite Sunday — minus the guilt, plus the caffeine.

---

Want me to adjust tone, trim the "Pitch" lines, or reorder labels once you share the actual Brand Kit format?

### Cheryl Subacius

Yes. the brand kit is: House bean card (the format every bean card follows):

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
Reply: This made our whole roasting crew's morning. We'll keep doing the thing.

Comment: Can I pause my subscription while I travel?
Reply: Yep. Account, then Subscription, then Pause. Your beans will wait for you, mostly patiently.

Pop-up location data (weekly figures from comparable past events):

Riverside Farmers Market: 9,000 visitors per week; 2% of visitors buy; average sale $14 (mostly whole-bean bags); rent $900 per week.
Union Station concourse: 30,000 visitors per week; 0.5% of visitors buy; average sale $6 (mostly single cups); rent $2,000 per week.
Campus library atrium: 6,000 visitors per week; 3% of visitors buy; average sale $5 (single cups); rent $600 per week.


### Claude

Got it — thanks for sharing the real format. Here are the three bean cards matching the house style exactly:

---

**YIRGACHEFFE, ETHIOPIA**
Roast: Light
Tastes like: jasmine, lemon, bergamot
Brew it: Pour-over
Real talk: Smells like a flower shop, drinks like a fancy breakfast. Rush it and you'll miss the point entirely.

---

**CERRADO, BRAZIL**
Roast: Medium-dark
Tastes like: peanut, milk chocolate, low acidity
Brew it: Espresso or French press
Real talk: Low acid, zero drama. The coffee equivalent of a weighted blanket.

---

**CHIAPAS, MEXICO**
Roast: Medium
Tastes like: almond, caramel, orange peel
Brew it: Drip or AeroPress
Real talk: Caramel and orange peel sounds like a candle. Good news: it tastes a lot better than one.

## Reflection

The one-shot bean card in Task 2 made the biggest difference, and the run shows it directly. With no example, Claude said it had no house format and invented one, with labels like "Tasting Notes" and "The Pitch"; after I pasted the single Huila card, it produced three cards with the exact labels (Roast, Tastes like, Brew it, Real talk) in the right order. Task 1's zero-shot perks met every rule (six numbered ideas of 10 to 14 words), but they read more like generic marketing ("Enjoy free priority shipping") than Wildframe's voice, and Claude opened by repeating my setup notes because I pasted them into the prompt. Task 3's few-shot replies captured the voice best, but reply 2 promised a "Swiss Water decaf" that is not in the Brand Kit, so examples teach tone, not facts. Task 4's chain-of-thought gave the most trustworthy answer: asked for step-by-step reasoning, Claude worked through six steps (buyers, revenue, weekly profit, the four-week rent check, total profit, conclusion), found Riverside earns $6,480 over four weeks against $1,200 for the library while Union Station loses money and its $8,000 rent breaks the budget, and recommended Riverside Farmers Market. Every number checks out, which I could only verify because the steps were shown. The choice I am least sure of is Task 2: to supply the bean card I pasted the whole Brand Kit, which also contained four past replies and the location data, so the prompt held more than the one example a one-shot prompt should. Next time I would paste only the Huila card, and I would trim the Brand Kit out of Task 4 as well, since that decision only needs the location data.
