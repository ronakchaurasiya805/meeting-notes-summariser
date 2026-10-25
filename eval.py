import time
from extractor import extract, NAIVE_PROMPT
from grounding import ground
from verifier import verify_owners

RUNS = 3    # each transcript is run this many times (LLM output varies)
PAUSE = 5   # seconds between calls, to stay inside free-tier limits

CASES = [
    {
        "name": "soft_commitment",
        "transcript": """Priya: Who can update the pricing page?
Sneha: Hmm, I might be able to look at it, but I'm not sure.
Priya: Okay, let's see how the week goes.""",
        "forbidden_owners": ["Sneha"],
        "forbidden_dates": [],
    },
    {
        "name": "suggested_not_agreed",
        "transcript": """Amit: I think Neha is the best person to prepare the slides.
Priya: Okay, we'll see.
Neha: I'm swamped this week, I can't take anything new.""",
        "forbidden_owners": ["Neha", "Amit"],
        "forbidden_dates": [],
    },
    {
        "name": "unrelated_date",
        "transcript": """Priya: The office is closed on Friday for the holiday.
Rahul: I'll send the contract to legal.
Priya: Great, thanks everyone.""",
        "forbidden_owners": [],
        "forbidden_dates": ["Friday"],
    },
    {
        "name": "already_done",
        "transcript": """Rahul: I already sent the proposal to the client yesterday.
Priya: Perfect. Sneha, anything on your side?
Sneha: No, all good here.""",
        "forbidden_owners": ["Rahul", "Sneha"],
        "forbidden_dates": [],
    },
    {
        "name": "declined_then_reassigned",
        "transcript": """Priya: Rahul, can you take the vendor call?
Rahul: Sorry, I'm on leave all week.
Priya: Okay, Sneha, can you?
Sneha: Sure, I'll take it.""",
        "forbidden_owners": ["Rahul"],
        "forbidden_dates": [],
    },
    {
        "name": "attendee_list",
        "transcript": """Attendees: Priya, Rahul, Sneha, Amit
Priya: We have to migrate the database before the audit.
Priya: That is the top priority this month.""",
        "forbidden_owners": ["Rahul", "Sneha", "Amit"],
        "forbidden_dates": [],
    },
    {
        "name": "role_assumption",
        "transcript": """Priya: The design review needs to happen soon.
Priya: Amit is the design lead, by the way.
Amit: Right.""",
        "forbidden_owners": ["Amit"],
        "forbidden_dates": [],
    },
    {
        "name": "relative_date",
        "transcript": """Rahul: I'll send the proposal after the demo.
Priya: The demo is on the 14th.""",
        "forbidden_owners": [],
        "forbidden_dates": ["14"],
    },
    {
        "name": "hinglish",
        "transcript": """Priya: Client ko proposal kaun bhejega?
Rahul: Main bhej dunga, kal tak.
Amit: Mujhe bhi ek copy chahiye.""",
        "forbidden_owners": ["Amit"],
        "forbidden_dates": [],
    },
]


def violations(result, case):
    n = 0
    for it in result.action_items:
        if it.owner and any(f.lower() in it.owner.lower() for f in case["forbidden_owners"]):
            n += 1
        if it.due_date and any(d.lower() in it.due_date.lower() for d in case["forbidden_dates"]):
            n += 1
    return n


def main():
    cols = ["naive", "rules", "ground", "final"]
    totals = {c: 0 for c in cols}
    done_runs = 0
    print(f"{'case':<28}{'naive':>7}{'rules':>7}{'+ground':>9}{'final':>7}")
    for case in CASES:
        t = case["transcript"]
        row = {c: 0 for c in cols}
        for _ in range(RUNS):
            try:
                naive = extract(t, NAIVE_PROMPT)
                rules = extract(t)
                grounded, _ = ground(rules, t)
                final, _ = verify_owners(grounded, t)
            except Exception as e:
                print(f"  error in {case['name']}: {str(e)[:120]}")
                time.sleep(PAUSE * 4)
                continue
            row["naive"] += violations(naive, case)
            row["rules"] += violations(rules, case)
            row["ground"] += violations(grounded, case)
            row["final"] += violations(final, case)
            done_runs += 1
            time.sleep(PAUSE)
        print(
            f"{case['name']:<28}{row['naive']:>7}{row['rules']:>7}"
            f"{row['ground']:>9}{row['final']:>7}"
        )
        for c in cols:
            totals[c] += row[c]

    print(
        f"{'TOTAL':<28}{totals['naive']:>7}{totals['rules']:>7}"
        f"{totals['ground']:>9}{totals['final']:>7}"
    )
    print(f"\nRuns completed: {done_runs} (violations = invented owners/dates, lower is better)")


if __name__ == "__main__":
    main()