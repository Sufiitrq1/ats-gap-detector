"""
Two-stage analysis:
  1. Extract structured requirements from the raw JD text.
  2. Semantically compare those requirements against the resume text
     and produce a gap report (have / weak / missing) with concrete
     next-step suggestions for each gap.

Both stages call Claude and force JSON-only output so the API layer
can render/email it without any regex scraping.
"""
import json
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"


def _call_json(system: str, user: str, max_tokens: int = 2000) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    # strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def extract_jd_requirements(jd_text: str) -> dict:
    system = (
        "You extract structured hiring requirements from a job description. "
        "Return ONLY valid JSON, no preamble, no markdown fences. "
        "Group requirements into competency clusters, not raw keywords "
        "(e.g. 'Kubernetes orchestration' not just 'Kubernetes'). "
        "Distinguish must-have from nice-to-have based on the JD's own language "
        "(e.g. 'required', 'must', 'plus', 'bonus', 'preferred')."
    )
    user = f"""Job description:
---
{jd_text}
---

Return JSON with this exact shape:
{{
  "role_title": "string",
  "seniority": "intern | entry-level | mid | senior | unclear",
  "must_have": [
    {{"skill": "string", "detail": "1-line clarification of what this means in context"}}
  ],
  "nice_to_have": [
    {{"skill": "string", "detail": "1-line clarification"}}
  ]
}}"""
    return _call_json(system, user)


def analyze_gap(resume_text: str, jd_requirements: dict) -> dict:
    system = (
        "You are a technical recruiter doing a SEMANTIC gap analysis, not a keyword search. "
        "A candidate can satisfy a requirement even if the exact term doesn't appear in their "
        "resume, if their described projects/experience demonstrate the underlying skill. "
        "Conversely, a term appearing once in a skills list with no supporting evidence is 'weak', "
        "not 'have'. Return ONLY valid JSON, no preamble, no markdown fences."
    )
    user = f"""Candidate resume:
---
{resume_text}
---

Job requirements (already extracted):
---
{json.dumps(jd_requirements, indent=2)}
---

For EVERY item in must_have and nice_to_have, classify it and return JSON with this exact shape:
{{
  "match_score": 0-100,
  "summary": "2-3 sentence honest overview of fit for this role",
  "have": [
    {{"skill": "string", "evidence": "what in the resume demonstrates this"}}
  ],
  "weak": [
    {{"skill": "string", "why_weak": "string", "fix": "specific action to strengthen resume wording/framing (not new skill-building, just better presentation)"}}
  ],
  "missing": [
    {{"skill": "string", "why_it_matters": "string", "how_to_close_gap": "concrete next step: a specific project idea, course, or certification with enough detail to act on immediately"}}
  ]
}}

Rules:
- "have" = clearly demonstrated with real evidence in the resume.
- "weak" = mentioned but thin, vague, or unsupported by concrete evidence.
- "missing" = not evidenced anywhere in the resume.
- match_score should reflect must_have coverage most heavily; nice_to_have matters less.
- Be specific and honest, not encouraging for its own sake."""
    return _call_json(system, user, max_tokens=3000)


def run_full_analysis(resume_text: str, jd_text: str) -> dict:
    jd_requirements = extract_jd_requirements(jd_text)
    gap_report = analyze_gap(resume_text, jd_requirements)
    return {
        "jd_requirements": jd_requirements,
        "gap_report": gap_report,
    }
