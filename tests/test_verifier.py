import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import MeetingSummary, ActionItem
from verifier import verify_owners

T_VENDOR = """Priya: We need someone to call the vendor about the late delivery.
Priya: Rahul usually handles vendors, but he's on leave this week.
Amit: Let's revisit this next meeting."""

T_TEAM = """Rahul: I'll send the updated proposal to the client by Friday.
Priya: Sneha, can you check the cloud bill and report back on Monday?
Sneha: Sure, I'll do that."""


def make(item):
    return MeetingSummary(summary="x", decisions=[], action_items=[item])


def test_mentioned_but_not_committed_is_removed():
    item = ActionItem(
        task="Call the vendor", owner="Rahul", due_date=None,
        evidence_quote="Rahul usually handles vendors, but he's on leave this week.",
    )
    clean, flags = verify_owners(make(item), T_VENDOR)
    assert clean.action_items[0].owner is None


def test_explicit_commitment_is_kept():
    item = ActionItem(
        task="Send the updated proposal", owner="Rahul", due_date="by Friday",
        evidence_quote="I'll send the updated proposal to the client by Friday.",
    )
    clean, flags = verify_owners(make(item), T_TEAM)
    assert clean.action_items[0].owner == "Rahul"


def test_commitment_in_next_line_is_kept():
    item = ActionItem(
        task="Check the cloud bill", owner="Sneha", due_date="on Monday",
        evidence_quote="Sneha, can you check the cloud bill and report back on Monday?",
    )
    clean, flags = verify_owners(make(item), T_TEAM)
    assert clean.action_items[0].owner == "Sneha"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError:
            print("FAIL", t.__name__)