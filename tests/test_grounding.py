import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import MeetingSummary, ActionItem
from grounding import ground

TRANSCRIPT = """Priya: We need someone to call the vendor about the late delivery.
Priya: Rahul usually handles vendors, but he's on leave this week.
Amit: Let's revisit this next meeting.
Priya: Fine. Also the report should be finished by end of month."""


def make(item):
    return MeetingSummary(summary="x", decisions=[], action_items=[item])


def test_valid_item_passes():
    item = ActionItem(
        task="Finish the report", owner=None, due_date="end of month",
        evidence_quote="Also the report should be finished by end of month.",
    )
    clean, flags = ground(make(item), TRANSCRIPT)
    assert len(clean.action_items) == 1
    assert flags == []


def test_fabricated_quote_is_dropped():
    item = ActionItem(
        task="Book a room", owner="Amit", due_date=None,
        evidence_quote="Amit: I will book the conference room tomorrow.",
    )
    clean, flags = ground(make(item), TRANSCRIPT)
    assert clean.action_items == []
    assert any("DROPPED" in f for f in flags)


def test_invented_owner_is_removed():
    item = ActionItem(
        task="Call the vendor", owner="Amit", due_date=None,
        evidence_quote="We need someone to call the vendor about the late delivery.",
    )
    clean, flags = ground(make(item), TRANSCRIPT)
    assert clean.action_items[0].owner is None
    assert any("OWNER REMOVED" in f for f in flags)


def test_invented_due_date_is_removed():
    item = ActionItem(
        task="Finish the report", owner=None, due_date="Friday",
        evidence_quote="Also the report should be finished by end of month.",
    )
    clean, flags = ground(make(item), TRANSCRIPT)
    assert clean.action_items[0].due_date is None
    assert any("DUE DATE REMOVED" in f for f in flags)


def test_KNOWN_GAP_name_in_line_but_no_commitment():
    # Rahul's name IS in this line, but he never took the task.
    # The simple string check cannot catch this yet (an LLM verifier will).
    item = ActionItem(
        task="Call the vendor", owner="Rahul", due_date=None,
        evidence_quote="Rahul usually handles vendors, but he's on leave this week.",
    )
    clean, flags = ground(make(item), TRANSCRIPT)
    assert clean.action_items[0].owner == "Rahul"  # flip this once the verifier exists


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError:
            print("FAIL", t.__name__)