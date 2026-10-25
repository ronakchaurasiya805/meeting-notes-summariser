import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import MeetingSummary, ActionItem
from grounding import ground


def make(item):
    return MeetingSummary(summary="x", decisions=[], action_items=[item])


def test_date_in_next_line_is_kept():
    t = """Priya: Sneha, can you book the venue?
Sneha: Yes, on it. I'll confirm by Monday."""
    item = ActionItem(
        task="Book the venue", owner="Sneha", due_date="Monday",
        evidence_quote="Sneha, can you book the venue?",
    )
    clean, flags = ground(make(item), t)
    assert clean.action_items[0].due_date == "Monday"


def test_date_far_away_is_removed():
    t = """Priya: Sneha, can you book the venue?
Amit: Noted.
Rahul: Sure.
Priya: The office is closed on Friday."""
    item = ActionItem(
        task="Book the venue", owner="Sneha", due_date="Friday",
        evidence_quote="Sneha, can you book the venue?",
    )
    clean, flags = ground(make(item), t)
    assert clean.action_items[0].due_date is None


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError:
            print("FAIL", t.__name__)