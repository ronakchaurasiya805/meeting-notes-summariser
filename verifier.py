from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from schema import MeetingSummary

load_dotenv()


class Verdict(BaseModel):
    # reason comes first so the model thinks before it decides
    reason: str = Field(description="One short sentence citing the transcript")
    owner_committed: bool = Field(
        description="True only if the owner explicitly committed to the task "
        "or was directly asked and accepted it."
    )


judge = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite").with_structured_output(Verdict)

SYSTEM_PROMPT = """You are a strict fact-checker for meeting notes.

You get a meeting transcript, a task, and a claimed owner.
Decide whether the claimed owner EXPLICITLY committed to the task
(e.g. "I'll do it") or was directly asked and accepted (look at the lines after the request too).

Answer false if:
- the person is only mentioned (e.g. "Rahul usually handles vendors")
- the task was phrased as "someone should..." and nobody took it
- the person said they are unavailable, or only gave an opinion or a maybe
"""


def verify_owners(result: MeetingSummary, transcript: str):
    flags, kept = [], []
    for item in result.action_items:
        if item.owner is None:
            kept.append(item)
            continue

        verdict = judge.invoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    f"TRANSCRIPT:\n{transcript}\n\n"
                    f"TASK: {item.task}\nCLAIMED OWNER: {item.owner}",
                ),
            ]
        )

        if verdict.owner_committed:
            kept.append(item)
        else:
            flags.append(
                f"OWNER REMOVED by verifier ('{item.owner}'): {item.task} | {verdict.reason}"
            )
            kept.append(item.model_copy(update={"owner": None}))

    return result.model_copy(update={"action_items": kept}), flags