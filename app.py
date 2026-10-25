import streamlit as st
from extractor import extract
from grounding import ground
from verifier import verify_owners

st.set_page_config(page_title="Meeting Notes Summariser", layout="wide")
st.title("Meeting Notes Summariser")
st.caption(
    "Extraction, then a grounding check, then an owner verifier. "
    "Owners and due dates the transcript does not support are removed and listed below."
)

SAMPLE = """Priya: Okay team, let's start. First, the client demo is moving to next Thursday.
Rahul: I'll send the updated proposal to the client by Friday.
Priya: Great. Also, someone should update the website with the new pricing.
Amit: The server costs are higher than expected, we should look at that.
Priya: Yes. Sneha, can you check the cloud bill and report back on Monday?
Sneha: Sure, I'll do that.
Priya: Alright, we decided to keep the current pricing for now. Thanks everyone."""

transcript = st.text_area("Paste a meeting transcript", value=SAMPLE, height=260)

if st.button("Summarise", type="primary") and transcript.strip():
    try:
        with st.spinner("Extracting and verifying..."):
            raw = extract(transcript)
            grounded, flags1 = ground(raw, transcript)
            final, flags2 = verify_owners(grounded, transcript)
    except Exception as e:
        st.error(f"Something went wrong (a free-tier rate limit is the usual cause): {str(e)[:200]}")
        st.stop()

    st.subheader("Summary")
    st.write(final.summary)

    st.subheader("Decisions")
    if final.decisions:
        for d in final.decisions:
            st.write(f"- {d}")
    else:
        st.write("None")

    st.subheader("Action items")
    rows = [
        {
            "Task": it.task,
            "Owner": it.owner or "unassigned",
            "Due": it.due_date or "none stated",
            "Evidence": it.evidence_quote,
        }
        for it in final.action_items
    ]
    st.dataframe(rows, use_container_width=True)

    st.subheader("Checks")
    flags = flags1 + flags2
    if flags:
        for f in flags:
            st.warning(f)
    else:
        st.success("All owners and due dates verified against the transcript.")

    with st.expander("Raw JSON"):
        st.code(final.model_dump_json(indent=2), language="json")