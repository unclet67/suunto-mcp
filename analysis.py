"""Core analysis logic for the Cyber Intel Teaching Converter.

This module holds the prompt engineering and the OpenAI call. It is kept
separate from the Streamlit UI (app.py) so it can be tested or reused on its
own. Nothing here writes report text to disk.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI

DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.2

# The exact set of sections we ask the model to return, described as a JSON
# contract. Keeping the shape explicit here (rather than free-form prose) is
# what lets the UI render each section deterministically.
JSON_CONTRACT = """
Return a single JSON object with EXACTLY these keys and shapes:

{
  "bluf": "string - Bottom Line Up Front, 1-3 sentences.",
  "key_entities": [
    {"name": "string", "type": "actor|victim|tool|infrastructure|organization|location|other",
     "role": "string - what this entity did or represents", "notes": "string"}
  ],
  "timeline": [
    {"when": "string - date/time or relative marker, or 'unspecified'",
     "event": "string - what happened"}
  ],
  "cit_matrix": {
    "actor": {"capability": "string", "intent": "string", "target": "string"},
    "victim": {"capability": "string", "intent": "string", "target": "string"}
  },
  "diamond_model": {
    "adversary": "string",
    "capability": "string",
    "infrastructure": "string",
    "victim": "string",
    "notes": "string - meta-features: timestamp, phase, direction, methodology, resources"
  },
  "attack_tactics": [
    {"tactic": "string - ATT&CK tactic name",
     "technique": "string - technique name and ID if inferable, else ''",
     "confidence": "high|medium|low",
     "note": "string - why this confidence; what evidence supports or is missing"}
  ],
  "pirs": ["string - Priority Intelligence Requirement phrased as a question"],
  "eeis": ["string - Essential Element of Information supporting the PIRs"],
  "intelligence_gaps": ["string - what is unknown or unconfirmed in the report"],
  "operational_relevance": "string - why this matters to a defender/operator, 2-4 sentences.",
  "teaching_points": ["string - discrete lesson takeaway for students"],
  "discussion_questions": ["string", "string", "string"],
  "classroom_vignette": "string - a short (4-8 sentence) scenario an instructor can read aloud.",
  "slide_takeaway": "string - one crisp line suitable as a single slide's headline."
}

Rules:
- "discussion_questions" MUST contain exactly three items.
- Base every field ONLY on the provided report. Do not invent named entities,
  dates, or indicators that are not present or reasonably inferable.
- When the report does not support a field, say so plainly (e.g. "Not stated
  in report") rather than fabricating.
- ATT&CK tactics are TENTATIVE: always include a confidence level and explain it.
- Output valid JSON only. No markdown, no commentary outside the JSON object.
"""

SYSTEM_PROMPT = (
    "You are a cyber threat intelligence instructor's assistant. You convert an "
    "unclassified incident or threat report into structured teaching material for "
    "a classroom setting. You are rigorous about analytic tradecraft: you "
    "distinguish evidence from inference, flag confidence, and never overstate "
    "attribution. You work only from the text provided.\n\n" + JSON_CONTRACT
)


def get_client(api_key: str | None = None) -> OpenAI:
    """Build an OpenAI client. Reads OPENAI_API_KEY from the environment if not given."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No OpenAI API key found. Set OPENAI_API_KEY in your .env file "
            "(see .env.example)."
        )
    return OpenAI(api_key=key)


def analyze_report(
    report_text: str,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> Dict[str, Any]:
    """Send the report to OpenAI and return the parsed structured analysis.

    Raises RuntimeError with a friendly message on missing key/empty input, and
    lets API/JSON errors propagate to be surfaced by the caller.
    """
    text = (report_text or "").strip()
    if not text:
        raise RuntimeError("Report text is empty. Paste an unclassified report first.")

    client = client or get_client()
    model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    if temperature is None:
        temperature = float(os.getenv("OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE))

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Convert the following UNCLASSIFIED report into the JSON "
                    "teaching structure defined in your instructions.\n\n"
                    "=== REPORT START ===\n"
                    f"{text}\n"
                    "=== REPORT END ==="
                ),
            },
        ],
    )

    content = response.choices[0].message.content or "{}"
    return json.loads(content)
