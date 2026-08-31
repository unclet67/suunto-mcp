"""Cyber Intel Teaching Converter — a local Streamlit app.

Paste an UNCLASSIFIED cyber report, click Analyze, and get instructor-ready
teaching material back: BLUF, entities, timeline, a Capability/Intent/Target
matrix, Diamond Model mapping, tentative ATT&CK tactics, PIRs/EEIs, gaps,
operational relevance, teaching points, discussion questions, a classroom
vignette, and a one-line slide takeaway.

Nothing is stored. The report text lives only in the current browser session's
memory while the app runs, and is sent to OpenAI solely to produce the analysis.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv

from analysis import DEFAULT_MODEL, analyze_report, get_client

load_dotenv()

st.set_page_config(
    page_title="Cyber Intel Teaching Converter",
    page_icon="🛡️",
    layout="wide",
)


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #
def _get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safe getter so a missing model key never crashes the render."""
    value = d.get(key, default)
    return value if value is not None else default


def render_list(items: Any, empty: str = "_Nothing returned._") -> None:
    items = items or []
    if not isinstance(items, list) or not items:
        st.markdown(empty)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_entities(entities: Any) -> None:
    entities = entities or []
    if not entities:
        st.markdown("_No entities identified._")
        return
    rows = [
        {
            "Name": _get(e, "name", ""),
            "Type": _get(e, "type", ""),
            "Role": _get(e, "role", ""),
            "Notes": _get(e, "notes", ""),
        }
        for e in entities
        if isinstance(e, dict)
    ]
    st.table(rows)


def render_timeline(timeline: Any) -> None:
    timeline = timeline or []
    if not timeline:
        st.markdown("_No timeline could be reconstructed._")
        return
    rows = [
        {"When": _get(t, "when", ""), "Event": _get(t, "event", "")}
        for t in timeline
        if isinstance(t, dict)
    ]
    st.table(rows)


def render_cit_matrix(matrix: Any) -> None:
    matrix = matrix or {}
    actor = _get(matrix, "actor", {}) or {}
    victim = _get(matrix, "victim", {}) or {}
    rows = [
        {
            "Party": "Actor",
            "Capability": _get(actor, "capability", ""),
            "Intent": _get(actor, "intent", ""),
            "Target": _get(actor, "target", ""),
        },
        {
            "Party": "Victim",
            "Capability": _get(victim, "capability", ""),
            "Intent": _get(victim, "intent", ""),
            "Target": _get(victim, "target", ""),
        },
    ]
    st.table(rows)


def render_diamond(diamond: Any) -> None:
    diamond = diamond or {}
    cols = st.columns(2)
    cols[0].markdown(f"**Adversary**\n\n{_get(diamond, 'adversary', '—')}")
    cols[1].markdown(f"**Capability**\n\n{_get(diamond, 'capability', '—')}")
    cols2 = st.columns(2)
    cols2[0].markdown(f"**Infrastructure**\n\n{_get(diamond, 'infrastructure', '—')}")
    cols2[1].markdown(f"**Victim**\n\n{_get(diamond, 'victim', '—')}")
    notes = _get(diamond, "notes", "")
    if notes:
        st.caption(f"Meta-features: {notes}")


def render_attack(tactics: Any) -> None:
    tactics = tactics or []
    if not tactics:
        st.markdown("_No ATT&CK tactics inferred._")
        return
    rows = [
        {
            "Tactic": _get(t, "tactic", ""),
            "Technique": _get(t, "technique", ""),
            "Confidence": _get(t, "confidence", ""),
            "Note": _get(t, "note", ""),
        }
        for t in tactics
        if isinstance(t, dict)
    ]
    st.table(rows)


# --------------------------------------------------------------------------- #
# Sidebar — config + safety reminder
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("Setup")
    key_present = bool(os.getenv("OPENAI_API_KEY"))
    if key_present:
        st.success("OPENAI_API_KEY detected.")
    else:
        st.error("No OPENAI_API_KEY found. Copy .env.example to .env and add your key.")

    model = st.text_input(
        "Model",
        value=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="Any OpenAI chat model that supports JSON output (e.g. gpt-4o, gpt-4o-mini).",
    )
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(os.getenv("OPENAI_TEMPERATURE", 0.2)),
        step=0.1,
        help="Lower = more deterministic and repeatable.",
    )
    st.divider()
    st.caption(
        "Privacy: this app stores nothing. Pasted text is held only in memory "
        "for the current session and sent to OpenAI to generate the analysis."
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
st.title("🛡️ Cyber Intel Teaching Converter")
st.markdown(
    "Turn an unclassified cyber report into instructor-ready teaching material."
)

st.warning(
    "⚠️ **UNCLASSIFIED USE ONLY.** Paste only unclassified, releasable text. "
    "Do not enter classified, CUI, or otherwise sensitive/proprietary material — "
    "input is sent to the OpenAI API.",
    icon="⚠️",
)

report_text = st.text_area(
    "Paste unclassified report text",
    height=280,
    placeholder="Paste the body of an unclassified incident or threat report here…",
)

col_a, col_b = st.columns([1, 4])
analyze_clicked = col_a.button("Analyze", type="primary", use_container_width=True)
if col_b.button("Clear", use_container_width=False):
    st.rerun()

if analyze_clicked:
    if not report_text.strip():
        st.error("Paste some report text first.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY in your .env file before analyzing.")
    else:
        try:
            with st.spinner("Analyzing report…"):
                client = get_client()
                result = analyze_report(
                    report_text,
                    client=client,
                    model=model,
                    temperature=temperature,
                )
        except Exception as exc:  # surface any API/JSON error cleanly
            st.error(f"Analysis failed: {exc}")
        else:
            st.success("Analysis complete.")

            st.subheader("BLUF")
            st.markdown(_get(result, "bluf", "_No BLUF returned._"))

            st.subheader("Slide Takeaway")
            st.info(_get(result, "slide_takeaway", "_No takeaway returned._"))

            st.subheader("Key Entities")
            render_entities(_get(result, "key_entities"))

            st.subheader("Timeline")
            render_timeline(_get(result, "timeline"))

            st.subheader("Capability / Intent / Target Matrix")
            render_cit_matrix(_get(result, "cit_matrix"))

            st.subheader("Diamond Model Mapping")
            render_diamond(_get(result, "diamond_model"))

            st.subheader("Tentative ATT&CK Tactics")
            st.caption("Tentative mappings — read the confidence and note for each.")
            render_attack(_get(result, "attack_tactics"))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("PIRs")
                render_list(_get(result, "pirs"))
            with col2:
                st.subheader("EEIs")
                render_list(_get(result, "eeis"))

            st.subheader("Intelligence Gaps")
            render_list(_get(result, "intelligence_gaps"))

            st.subheader("Operational Relevance")
            st.markdown(_get(result, "operational_relevance", "_None returned._"))

            st.subheader("Teaching Points")
            render_list(_get(result, "teaching_points"))

            st.subheader("Discussion Questions")
            render_list(_get(result, "discussion_questions"))

            st.subheader("Classroom Vignette")
            st.markdown(_get(result, "classroom_vignette", "_None returned._"))

            with st.expander("Raw JSON"):
                st.json(result)
