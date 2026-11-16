"""Intake: transcript -> persona JSON (SPEC section 4, Intake).

M1 ships the fixture loader. `extract_persona` builds the single LLM prompt;
the caller supplies `llm(prompt) -> str` so the model choice stays outside
this module. Output is always validated against the Persona schema.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from src.schemas import Persona, validate_persona

FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "personas"

EXTRACTION_PROMPT = """You convert a wellness intake transcript into JSON.
Return only a JSON object with these fields:
user_id (string), synthetic (true), goals (list of strings), conditions (list of strings),
medications (list of {{name, approved: bool}} where approved means FDA-approved prescription),
supplements_peptides (list of {{name, source, fda_approved: bool}}),
risk_tolerance (integer 1 to 5), readiness_to_act (integer 1 to 5),
source_trust (object with integer 1 to 5 for exactly: doctor, physician_creator, coach, reddit, influencer).
Use only what the user said. Do not add dosing information.

user_id: {user_id}
Transcript:
{transcript}
"""


def load_persona(persona_id: str = "p-001") -> Persona:
    return validate_persona(json.loads((FIXTURES / f"{persona_id}.json").read_text(encoding="utf-8")))


def load_transcript(persona_id: str = "p-001") -> str:
    return (FIXTURES / f"{persona_id}_transcript.txt").read_text(encoding="utf-8")


def extract_persona(transcript: str, user_id: str, llm: Callable[[str], str]) -> Persona:
    raw = llm(EXTRACTION_PROMPT.format(user_id=user_id, transcript=transcript))
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return validate_persona(json.loads(raw))
