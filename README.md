# Cyber Intel Teaching Converter

A small, local [Streamlit](https://streamlit.io/) app that turns an
**unclassified** cyber report into instructor-ready teaching material. Paste a
report, click **Analyze**, and the app calls the OpenAI API and returns a
structured breakdown you can drop straight into a lesson.

## What it produces

For each report the app returns:

- **BLUF** — bottom line up front
- **Key entities** — actors, victims, tools, infrastructure, orgs
- **Timeline** — reconstructed sequence of events
- **Capability / Intent / Target matrix** — actor vs. victim
- **Diamond Model mapping** — adversary, capability, infrastructure, victim (+ meta-features)
- **Tentative ATT&CK tactics** — each with a confidence level and a note explaining it
- **PIRs and EEIs** — priority intelligence requirements and their essential elements
- **Intelligence gaps** — what the report leaves unknown
- **Operational relevance** — why a defender/operator should care
- **Teaching points** — discrete lesson takeaways
- **Three discussion questions**
- **A short classroom vignette** an instructor can read aloud
- **One slide takeaway** — a single headline line

> ⚠️ **UNCLASSIFIED USE ONLY.** Paste only unclassified, releasable text. Do not
> enter classified, CUI, or otherwise sensitive/proprietary material — the input
> is sent to the OpenAI API.

## Privacy

The app **stores nothing**. Report text is held only in the current Streamlit
session's memory while the app runs, and is sent to OpenAI solely to generate
the analysis. There is no database, no logging of report contents, and no local
file is written with your input.

## Requirements

- Python 3.9+
- An OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys))

## Setup

```bash
# 1. (recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. configure your API key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

### Environment variables

See [`.env.example`](.env.example). The `.env` file is git-ignored.

| Variable             | Required | Default   | Description                                   |
| -------------------- | -------- | --------- | --------------------------------------------- |
| `OPENAI_API_KEY`     | yes      | —         | Your OpenAI API key.                          |
| `OPENAI_MODEL`       | no       | `gpt-4o`  | Any chat model that supports JSON output.     |
| `OPENAI_TEMPERATURE` | no       | `0.2`     | Sampling temperature (lower = more repeatable). |

## Run

```bash
streamlit run app.py
```

Streamlit prints a local URL (typically <http://localhost:8501>). Open it, paste
an unclassified report, and click **Analyze**. You can override the model and
temperature from the sidebar per run.

## Project layout

```
app.py             # Streamlit UI and rendering
analysis.py        # Prompt + OpenAI call (JSON contract), UI-independent
requirements.txt   # Dependencies
.env.example       # Copy to .env and fill in
.gitignore         # Keeps .env and caches out of git
```

## Notes and limitations

- The ATT&CK mappings are **tentative** by design. Always read the per-tactic
  confidence and note; treat low-confidence items as prompts for discussion,
  not conclusions.
- Output quality tracks the input. Short or vague reports yield thinner
  analysis, and the model is instructed to say "Not stated in report" rather
  than fabricate details.
- The model can still make mistakes. Review the output before teaching from it.
```
