"""Demo data export (M5): writes app/demo_data.js (`window.DEMO = {...};`) for the static page.

Fighters are the persona-filtered clinical sources plus the real public posts. Each fighter
stands in the Medicine corner (expert_evidence / expert_opinion) or the Public corner,
decided by `classify_expert` per claim and never by platform.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.classify.expert import classify_expert
from src.intake.persona import load_persona
from src.respond import structured
from src.retrieval import clinical, public
from src.safety import redact_dosing
from src.schemas import Source

OUT = Path(__file__).resolve().parents[1] / "app" / "demo_data.js"
PERSONA_ID = "p-002"
QUESTION = "I'm on semaglutide and worried about muscle loss. Should I add BPC-157?"
PROBLEM = ("People on GLP-1s get conflicting advice from doctors, influencers, and Reddit. "
           "Second Opinion shows what the clinical evidence says, what real users say, and how much "
           "weight each claim deserves.")
MEDICINE_CATEGORIES = {"expert_evidence", "expert_opinion"}


def corner(category: str) -> str:
    return "medicine" if category in MEDICINE_CATEGORIES else "public"


def _majority(stances: list[str]) -> str | None:
    if not stances:
        return None
    ranked = Counter(stances).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "cautions"
    return ranked[0][0]


def topic_verdict(topic: dict, corner_by_id: dict[str, str]) -> dict:
    """Majority stance per corner (ties -> cautions); agree / split / one-sided."""
    by_corner: dict[str, list[str]] = {"medicine": [], "public": []}
    for sid, stance in topic["stances"].items():
        if sid in corner_by_id:
            by_corner[corner_by_id[sid]].append(stance)
    med, pub = _majority(by_corner["medicine"]), _majority(by_corner["public"])
    if med is None or pub is None:
        verdict = "one-sided"
    else:
        verdict = "agree" if med == pub else "split"
    return {"id": topic["id"], "topic": topic["topic"], "medicine": med, "public": pub, "verdict": verdict}


def _fighter(s: Source) -> dict:
    category, out_of_field = classify_expert(s)
    is_clinical = s.lane == "clinical"
    text, _ = redact_dosing(s.text)
    claim, _ = redact_dosing(s.title if is_clinical else (s.claim or s.title))
    return {
        "id": s.id, "lane": s.lane, "corner": corner(category), "expert_category": category,
        "out_of_field": out_of_field, "speaker": s.speaker, "credential": s.speaker_credential,
        "credential_verified": False if (not is_clinical and s.speaker_credential) else None,
        "platform": s.platform, "badge": clinical.journal_badge(s) if is_clinical else s.platform,
        "coi": s.coi, "claim": claim, "title": s.title, "url": s.url, "text": text,
        "synthetic": s.synthetic,
    }


def _persona_note(excluded: list[dict]) -> str:
    if not excluded:
        return "The evidence shown matches this persona; no studies were set aside."
    names = ", ".join(_short_title(e["title"]) for e in excluded)
    n = len(excluded)
    return (f"Because she has no diabetes, {n} {'trial' if n == 1 else 'trials'} in people with "
            f"type 2 diabetes {'was' if n == 1 else 'were'} set aside: {names}.")


def _short_title(title: str) -> str:
    """Trial acronym when the title carries one (STEP 2, SURMOUNT-2), else a trimmed title."""
    import re
    m = re.search(r"\b(STEP\s?\d+|SURMOUNT-\d+|SUSTAIN[- ]?\d+|SCALE|OASIS\s?\d+|PIONEER\s?\d+)\b", title)
    return m.group(1) if m else (title if len(title) <= 60 else title[:57].rstrip() + "...")


def build_demo_data() -> dict:
    persona = load_persona(PERSONA_ID)
    kept, excluded = structured.persona_filter(clinical.load_snapshot(), persona)
    posts = public.load_posts(public.REAL_POSTS)
    sources = [s for s in kept if s.lane == "clinical"] + posts
    fighters = [_fighter(s) for s in sources]
    corner_by_id = {f["id"]: f["corner"] for f in fighters}
    composed = {c["topic_id"]: c for c in structured.compose_all(persona, posts)}
    topics = []
    for t in structured.load_topics():
        c = composed[t["id"]]
        v = topic_verdict(t, corner_by_id)
        # `medicine`/`public` would collide with the response objects below, so they become *_stance.
        topics.append({"id": v["id"], "topic": v["topic"], "medicine_stance": v["medicine"],
                       "public_stance": v["public"], "verdict": v["verdict"], "clinical": c["clinical"], "public": c["public"],
                       "excluded_for_persona": c["excluded_for_persona"]})
    seen: dict[str, dict] = {}
    for t in topics:
        for e in t["excluded_for_persona"]:
            seen.setdefault(e["id"], e)
    excluded_all = list(seen.values())
    return {
        "product": "Second Opinion", "synthetic": True, "question": QUESTION, "problem": PROBLEM,
        "persona": persona.to_dict() if hasattr(persona, "to_dict") else persona.__dict__,
        "persona_note": _persona_note(excluded_all), "excluded_for_persona": excluded_all,
        "fighters": fighters, "topics": topics,
        "counts": {"medicine": sum(f["corner"] == "medicine" for f in fighters),
                   "public": sum(f["corner"] == "public" for f in fighters)},
    }


def write_demo_js(path: Path = OUT) -> Path:
    payload = json.dumps(build_demo_data(), ensure_ascii=False, indent=2).replace("</", "<\\/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"window.DEMO = {payload};\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    out = write_demo_js()
    data = json.loads(out.read_text(encoding="utf-8").removeprefix("window.DEMO = ").rstrip().rstrip(";"))
    print(f"wrote {out}: {len(data['fighters'])} fighters {data['counts']}")
    print(data["persona_note"])
    for t in data["topics"]:
        print(f"[{t['id']}] {t['verdict']} (medicine={t['medicine_stance']}, public={t['public_stance']})")
        print(f"  Medical evidence: {t['clinical']['text']}")
        print(f"  Court of public opinion: {t['public']['text']}")
