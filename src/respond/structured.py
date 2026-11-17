"""Structured response composer (M3): two fixed-template sentences per claim topic.

For each topic in data/fixtures/claim_topics.json:
- clinical sentence: summarises clinical sources tagged `supports` or `cautions`;
- public sentence: summarises the "court of public opinion" from public posts.

`finding` and `recommendation` are hand-written in the fixture today; an M3
generator may fill them later. Every sentence passes through `redact_dosing`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.retrieval import clinical, public
from src.safety import redact_dosing
from src.schemas import Source

TOPICS = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "claim_topics.json"
STANCES = {"supports", "opposes", "cautions"}
TOPIC_KEYS = ["id", "topic", "finding", "recommendation", "public_conclusion", "stances"]

CLINICAL_TEMPLATE = ("From {sources} sources (most reputable), we identified {n_studies} {studies_word} "
                     "with study sizes of {sizes}, with the main finding that {finding}. "
                     "Thus, we recommend {recommendation}.")
# No tagged clinical source: no finding and no recommendation (every recommendation needs a source).
CLINICAL_NONE = "We identified no studies in our clinical sources that test this claim."
PUBLIC_TEMPLATE = ("Across {platforms}, we identified {n_support} {posts_word} supporting "
                   "the conclusion that {public_conclusion}.")
PUBLIC_DISPUTED = " {n_oppose} {posts_word2} disputed it."
PUBLIC_NONE = "We identified no public posts on the conclusion that {public_conclusion}."

# Publication types that rank a journal ahead of others (systematic review / meta-analysis / RCT).
HIGH_TIER_TYPES = {"Systematic Review", "Meta-Analysis", "Randomized Controlled Trial"}
# A narrative review quotes other studies' numbers; those are not its own sample.
POOLED_REVIEW_TYPES = {"Systematic Review", "Meta-Analysis"}
BADGE_RANK = {"NEJM": 0, "Lancet": 1}

_NUM = r"\d{1,3}(?:[,\u2009\u202f]\d{3})+|\d+"  # 1,961 / 15<thin space>782 / 160
_PEOPLE = r"(?:participants|patients|adults|subjects|individuals|people|women|men|volunteers)"
_SIZE_PATTERNS = [
    re.compile(rf"\bn\s*=\s*({_NUM})", re.IGNORECASE),
    re.compile(rf"\b({_NUM})\s+{_PEOPLE}\b", re.IGNORECASE),
]
# Randomisation counts win over the largest-number rule, so a trial shows the number
# randomised rather than the number screened. "(?![:\d])" skips ratios such as "2:1".
_RANDOMISED_PATTERNS = [
    re.compile(rf"\brandomly\s+assigned\s+({_NUM})(?![:\d])", re.IGNORECASE),
    re.compile(rf"\brandomi[sz]ed\s+({_NUM})(?![:\d])", re.IGNORECASE),
    # "1210 were randomly assigned", "938 (mean age ...) were randomly assigned",
    # "1,407 participants were randomised"
    re.compile(rf"\b({_NUM})\s+(?:{_PEOPLE}\s+)?(?:\([^()]*\)\s*)?(?:were|was)\s+"
               rf"(?:randomly\s+assigned|randomi[sz]ed)", re.IGNORECASE),
    re.compile(rf"\b({_NUM})\s+(?:{_PEOPLE}\s+)?underwent\s+randomi[sz]ation", re.IGNORECASE),
]
_SCREENED_BEFORE = re.compile(r"screened\s*$", re.IGNORECASE)
MIN_SIZE = 5
MAX_LISTED_SIZES = 4


# ------------------------------------------------------------------ helpers

def _join(items: list[str]) -> str:
    """A / A and B / A, B and C."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _size_text(n: int | None) -> str:
    return "size not reported" if n is None else f"{n:,}"


def journal_name(source: Source) -> str:
    """Display name: "NEJM" or "Lancet" by badge, otherwise the MEDLINE abbreviation."""
    badge = clinical.journal_badge(source)
    if badge in BADGE_RANK:
        return badge
    return source.journal_abbrev or source.journal or "PubMed"


def _reputability_key(source: Source) -> tuple:
    badge_rank = BADGE_RANK.get(clinical.journal_badge(source), len(BADGE_RANK))
    tier_rank = 0 if HIGH_TIER_TYPES & set(source.publication_types) else 1
    return (badge_rank, tier_rank, journal_name(source).lower())


def study_size(source: Source) -> int | None:
    """Sample size for display; None for narrative reviews (Review without SR/MA)."""
    types = set(source.publication_types)
    if "Review" in types and not types & POOLED_REVIEW_TYPES:
        return None
    return extract_study_size(source.text)


REDACTED_FIELDS = ("text", "finding", "recommendation", "public_conclusion")


def _redacted(result: dict) -> dict:
    """Run every free-text field through redact_dosing; `redacted` is True if any changed."""
    result["redacted"] = False
    for key in REDACTED_FIELDS:
        if isinstance(result.get(key), str):
            result[key], hit = redact_dosing(result[key])
            result["redacted"] |= hit
    return result


# ------------------------------------------------------------------ public API

def load_topics(path: Path = TOPICS) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    topics = data["topics"]
    seen = set()
    for i, t in enumerate(topics):
        missing = [k for k in TOPIC_KEYS if k not in t]
        if missing:
            raise ValueError(f"claim_topics.json topics[{i}]: missing fields {missing}")
        if t["id"] in seen:
            raise ValueError(f"claim_topics.json: duplicate topic id {t['id']}")
        seen.add(t["id"])
        bad = {sid: s for sid, s in t["stances"].items() if s not in STANCES}
        if bad:
            raise ValueError(f"claim_topics.json {t['id']}: stances must be one of {sorted(STANCES)}, got {bad}")
    return topics


def _numbers(patterns: list[re.Pattern], text: str, skip_screened: bool = False) -> list[int]:
    out = []
    for p in patterns:
        for m in p.finditer(text):
            if skip_screened and _SCREENED_BEFORE.search(text, 0, m.start(1)):
                continue
            n = int(re.sub(r"\D", "", m.group(1)))
            if n >= MIN_SIZE:
                out.append(n)
    return out


def extract_study_size(text: str) -> int | None:
    """Sample size: the randomised count if stated, else the largest of "n = 1,234",
    "N=123", "1,961 adults" ... Numbers < 5 and numbers right after "screened" are ignored.
    """
    sizes = _numbers(_RANDOMISED_PATTERNS, text) or _numbers(_SIZE_PATTERNS, text, skip_screened=True)
    return max(sizes) if sizes else None


def _sizes_text(sizes: list[int | None]) -> str:
    """Up to 4 sizes as a list; more as "{n} reported sizes from {min} to {max} and {k} not reported"."""
    if len(sizes) <= MAX_LISTED_SIZES:
        return _join([_size_text(x) for x in sizes])
    reported = [x for x in sizes if x is not None]
    missing = len(sizes) - len(reported)
    if not reported:
        return f"size not reported for all {len(sizes)} studies"
    if len(reported) == 1:
        text = f"1 reported size of {reported[0]:,}"
    else:
        text = f"{len(reported)} reported sizes from {min(reported):,} to {max(reported):,}"
    return text + (f" and {missing} not reported" if missing else "")


def clinical_response(topic: dict, sources: list[Source]) -> dict:
    """Clinical sentence from sources tagged `supports` or `cautions`, most reputable first."""
    stances = topic["stances"]
    picked = [s for s in sources if s.lane == "clinical" and stances.get(s.id) in ("supports", "cautions")]
    picked.sort(key=_reputability_key)  # stable: ties keep input order
    names = list(dict.fromkeys(journal_name(s) for s in picked))[:3]
    sizes = [study_size(s) for s in picked]
    n = len(picked)
    if n:
        text = CLINICAL_TEMPLATE.format(
            sources=_join(names), n_studies=n, studies_word=_plural(n, "study", "studies"),
            sizes=_sizes_text(sizes),
            finding=topic["finding"], recommendation=topic["recommendation"])
    else:
        text = CLINICAL_NONE
    return _redacted({
        "topic_id": topic["id"],
        "sources": [s.id for s in picked],
        "journals": names,
        "n_studies": n,
        "study_sizes": sizes,
        "finding": topic["finding"] if n else None,
        "recommendation": topic["recommendation"] if n else None,
        "text": text,
    })


def public_response(topic: dict, posts: list[Source]) -> dict:
    """Public sentence: `supports` posts back the conclusion, `opposes` posts dispute it.

    `cautions` posts are not counted in either number (nor in platforms or n_synthetic).
    """
    stances = topic["stances"]
    counted = [p for p in posts if p.lane == "public" and stances.get(p.id) in ("supports", "opposes")]
    n_support = sum(stances[p.id] == "supports" for p in counted)
    n_oppose = len(counted) - n_support
    platforms = list(dict.fromkeys(p.platform for p in counted))
    if counted:
        text = PUBLIC_TEMPLATE.format(
            platforms=_join(platforms), n_support=n_support,
            posts_word=_plural(n_support, "post", "posts"),
            public_conclusion=topic["public_conclusion"])
        if n_oppose:
            text += PUBLIC_DISPUTED.format(n_oppose=n_oppose, posts_word2=_plural(n_oppose, "post", "posts"))
    else:
        text = PUBLIC_NONE.format(public_conclusion=topic["public_conclusion"])
    return _redacted({
        "topic_id": topic["id"],
        "post_ids": [p.id for p in counted],
        "platforms": platforms,
        "n_support": n_support,
        "n_oppose": n_oppose,
        "n_synthetic": sum(p.synthetic for p in counted),
        "public_conclusion": topic["public_conclusion"],
        "text": text,
    })


def compose_all() -> list[dict]:
    sources, posts = clinical.load_snapshot(), public.load_posts()
    return [{"topic_id": t["id"], "topic": t["topic"],
             "clinical": clinical_response(t, sources),
             "public": public_response(t, posts)}
            for t in load_topics()]


if __name__ == "__main__":
    for item in compose_all():
        print(f"[{item['topic_id']}] {item['topic']}")
        print(f"  Medical evidence: {item['clinical']['text']}")
        print(f"  Court of public opinion: {item['public']['text']}")
