import sys
from extractor import extract
from grounding import ground
from verifier import verify_owners


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        transcript = f.read()

    raw = extract(transcript)
    grounded, flags1 = ground(raw, transcript)
    final, flags2 = verify_owners(grounded, transcript)

    print(final.model_dump_json(indent=2))
    print("\n--- FLAGS ---")
    flags = flags1 + flags2
    print("\n".join(flags) if flags else "None (all items verified)")


if __name__ == "__main__":
    main() 