\# Meeting Notes Summariser



Paste a messy meeting transcript, get back a summary, decisions, and action items

with owners and due dates as \*\*validated structured data\*\*, not a paragraph.



The interesting part is not the summary. It is making sure the model \*\*never invents

an owner or a deadline\*\* that nobody actually committed to.



\## Why this is hard



LLMs happily fill gaps. In meeting transcripts the gaps are everywhere:



\- "Someone should update the website" has no owner.

\- "Rahul usually handles vendors, but he's on leave" mentions Rahul but he committed to nothing.

\- "Sneha: I might be able to look at it, but I'm not sure" is not a commitment.



Assigning any of these to a person is worse than leaving the owner empty.



\## How it works



```mermaid

flowchart LR

&#x20;   T\[Transcript] --> E\[1. Extraction<br/>LLM + Pydantic schema]

&#x20;   E --> G\[2. Grounding check<br/>pure Python]

&#x20;   G --> V\[3. Owner verifier<br/>second LLM call]

&#x20;   V --> O\[Clean structured output + flags]

```



1\. \*\*Extraction\*\* (`extractor.py`): the LLM returns a `MeetingSummary` validated against a

&#x20;  Pydantic schema. `owner` and `due\_date` are optional, and each action item must carry an

&#x20;  `evidence\_quote` copied from the transcript.

2\. \*\*Grounding check\*\* (`grounding.py`): no LLM involved. It finds the evidence quote in the

&#x20;  transcript (fuzzy match), drops items whose quote does not exist, and removes any owner or

&#x20;  due date that does not appear near that source line (the line itself or the next two).

3\. \*\*Owner verifier\*\* (`verifier.py`): a separate LLM call sees the whole transcript and answers

&#x20;  one narrow question: did this person explicitly commit to this task, or accept it when asked?

&#x20;  If not, the owner is set to `null`. This catches cases grounding cannot: the name is

&#x20;  present in the line, but the person never took the task.



Every removal is reported in a `FLAGS` section so nothing is silently changed.



\## Example



Input:



```

Priya: Also, someone should update the website with the new pricing.

Priya: Yes. Sneha, can you check the cloud bill and report back on Monday?

Sneha: Sure, I'll do that.

```



Output (trimmed):



```json

{

&#x20; "action\_items": \[

&#x20;   { "task": "Update the website with the new pricing", "owner": null, "due\_date": null },

&#x20;   { "task": "Check the cloud bill and report back", "owner": "Sneha", "due\_date": "on Monday" }

&#x20; ]

}

```



\## Evaluation



All numbers below are from small hand-written test sets. Treat them as an early signal, not a benchmark.



\*\*Adversarial transcripts\*\* (`eval.py`): 9 transcripts built to tempt the model (soft commitments,

people suggested but not agreed, attendee lists, role assumptions, unrelated dates, declined then

reassigned, relative dates, Hinglish), each run 3 times = 27 runs. A violation is an owner or due

date that must not appear in the output.



| Stage | Violations (27 runs) |

|---|---|

| Bare prompt (naive) | 1 |

| Strict rules prompt | 1 |

| + grounding | 1 |

| + owner verifier (final) | 0 |



\- The one violation that survived grounding was a soft commitment ("I might be able to look at

&#x20; it"). Grounding cannot catch it because the name is in the line. The verifier removed it.

\- Which test case fails varies between runs, which is why a single passing run proves little.



\*\*Recall check\*\* (`eval\_recall.py`): 15 correct owner/due-date items across 4 transcripts. Did the

layers remove anything that was right?



| | Correct items kept |

|---|---|

| Before fix | 14 / 15 |

| After fix | 15 / 15 |



\### A bug the recall check found



The grounding layer originally checked due dates only against the single evidence line.

When the model quoted "Sneha, can you book the venue?" (the request) while "I'll confirm by Monday"

was on the next line, a correct due date was removed. The fix was to also look at the following two

lines. Regression tests are in `tests/test\_grounding\_lookahead.py`, and the adversarial eval was

re-run to check the wider window did not let an unrelated date through.



\## Limitations



\- Small test sets (9 + 4 transcripts) and one model (`gemini-3.5-flash-lite`). Results may not hold on

&#x20; long, noisy, multi-speaker real meetings.

\- The "naive" baseline still benefits from the schema field descriptions ("null if not stated"),

&#x20; so it is not a fully naive comparison. The gap between naive and rules is therefore small.

\- The verifier checks \*\*owners only\*\*. Due dates are protected only by grounding's string match,

&#x20; which can be fooled by an unrelated date near the right line, or reject a correct paraphrase

&#x20; ("tomorrow" for "kal tak").

\- The verifier is itself an LLM and can be wrong. It was tested on 3 direct cases.

\- Extraction can still miss a task (recall of tasks is not measured, only owners and dates).



\## Setup



```bash

python -m venv venv

venv\\Scripts\\activate          # Windows

pip install -r requirements.txt

```



Create a `.env` file:



```

GOOGLE\_API\_KEY=your-key

```



The free Gemini API tier is enough for this project.



\## Run



```bash

python main.py transcripts/sample1.txt

```



\## Tests and evals



```bash

python tests/test\_grounding.py

python tests/test\_grounding\_lookahead.py

python tests/test\_verifier.py      # calls the API

python eval.py                     # adversarial set, calls the API

python eval\_recall.py              # recall check, calls the API

```



\## Stack



Python, LangChain, Pydantic, Google Gemini API.

