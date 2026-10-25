from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from schema import MeetingSummary

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
structured_llm = llm.with_structured_output(MeetingSummary)

SYSTEM_PROMPT = """You extract structured notes from meeting transcripts.

Rules:
- Use ONLY information explicitly stated in the transcript.
- Include EVERY task someone says needs to be done, even if nobody took it.
- An owner is someone who clearly commits to or is directly assigned the task.
  If nobody takes the task (e.g. "someone should..."), keep the task but set owner to null.
- If no deadline is stated for a task, due_date must be null.
- Never guess or invent names, dates, or tasks.
- evidence_quote must be copied word-for-word from the transcript.
"""

NAIVE_PROMPT = (
    "Summarize this meeting transcript and list the action items "
    "with owners and due dates."
)


def extract(transcript: str, prompt: str = SYSTEM_PROMPT) -> MeetingSummary:
    return structured_llm.invoke([("system", prompt), ("human", transcript)])