import time
from extractor import extract
from grounding import ground
from verifier import verify_owners

RUNS = 3
PAUSE = 5

# expected: owner -> due-date keyword the output should still contain (None = only check owner)
CASES = [
    {
        "name": "plain_commitment",
        "transcript": """Priya: Who will send the report?
Rahul: I'll send it by Wednesday.""",
        "expected": {"Rahul": "Wednesday"},
    },
    {
        "name": "assigned_and_accepted",
        "transcript": """Priya: Sneha, can you book the venue?
Sneha: Yes, on it. I'll confirm by Monday.""",
        "expected": {"Sneha": "Monday"},
    },
    {
        "name": "two_owners",
        "transcript": """Rahul: I'll draft the proposal by Tuesday.
Amit: And I'll review it on Thursday.""",
        "expected": {"Rahul": "Tuesday", "Amit": "Thursday"},
    },
    {
        "name": "hinglish_commitment",
        "transcript": """Priya: Client ko proposal kaun bhejega?
Rahul: Main bhej dunga, kal tak.""",
        "expected": {"Rahul": None},
    },
]


def found(result, name, due):
    for it in result.action_items:
        if it.owner and name.lower() in it.owner.lower():
            if due is None or (it.due_date and due.lower() in it.due_date.lower()):
                return True
    return False


def main():
    tot = {"n": 0, "rules": 0, "final": 0}
    print(f"{'case':<26}{'expected':>9}{'rules':>7}{'final':>7}")
    for case in CASES:
        t = case["transcript"]
        n = r_hit = f_hit = 0
        for _ in range(RUNS):
            try:
                rules = extract(t)
                grounded, _ = ground(rules, t)
                final, _ = verify_owners(grounded, t)
            except Exception as e:
                print(f"  error in {case['name']}: {str(e)[:120]}")
                time.sleep(PAUSE * 4)
                continue
            for name, due in case["expected"].items():
                n += 1
                r_hit += found(rules, name, due)
                f_hit += found(final, name, due)
            time.sleep(PAUSE)
        print(f"{case['name']:<26}{n:>9}{r_hit:>7}{f_hit:>7}")
        tot["n"] += n
        tot["rules"] += r_hit
        tot["final"] += f_hit
    print(f"{'TOTAL':<26}{tot['n']:>9}{tot['rules']:>7}{tot['final']:>7}")
    print("\nrules vs final: if final < rules, the layers removed correct owners/dates.")


if __name__ == "__main__":
    main()