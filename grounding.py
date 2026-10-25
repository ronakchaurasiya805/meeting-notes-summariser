import re
from difflib import SequenceMatcher
from schema import MeetingSummary

LOOKAHEAD = 2  # also look at the next N lines when checking the due date


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def find_source_line(quote: str, lines: list):
    """Return (index, score) of the transcript line that best matches the quote."""
    q = _norm(quote)
    best_i, best_score = None, 0.0
    for i, line in enumerate(lines):
        l = _norm(line)
        if not l:
            continue
        if q in l:
            return i, 1.0
        score = SequenceMatcher(None, q, l).ratio()
        if score > best_score:
            best_i, best_score = i, score
    return best_i, best_score


def _contains(line: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(text.lower())}\b", line.lower()) is not None


def _date_in_text(text: str, due: str) -> bool:
    core = re.sub(r"^(by|on|before|until|till)\s+", "", due.strip(), flags=re.I)
    return _norm(core) in _norm(text)


def ground(result: MeetingSummary, transcript: str):
    """Verify every action item against the transcript. Returns (clean_result, flags)."""
    lines = transcript.splitlines()
    flags, kept = [], []
    for item in result.action_items:
        i, score = find_source_line(item.evidence_quote, lines)

        if i is None or score < 0.85:
            flags.append(f"DROPPED (quote not found in transcript): {item.task}")
            continue

        line = lines[i]
        after = " ".join(lines[i + 1 : i + 1 + LOOKAHEAD])

        update = {}
        if item.owner and not _contains(line, item.owner):
            flags.append(f"OWNER REMOVED ('{item.owner}' not in source line): {item.task}")
            update["owner"] = None
        if item.due_date and not (
            _date_in_text(line, item.due_date) or _date_in_text(after, item.due_date)
        ):
            flags.append(f"DUE DATE REMOVED ('{item.due_date}' not near source line): {item.task}")
            update["due_date"] = None

        kept.append(item.model_copy(update=update))

    return result.model_copy(update={"action_items": kept}), flags