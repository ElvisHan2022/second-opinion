"""Data objects for Credence (SPEC section 3) and plain validators.

Every LLM output that feeds code is validated here before use. Validators
raise ValueError with a message naming the bad field; they never coerce.
Stdlib only, so the demo has no schema-library dependency.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

LANES = {"clinical", "public"}
COI = {"yes", "no", "unknown"}
EXPERT_CATEGORIES = {"expert_evidence", "expert_opinion", "relayed_evidence", "anecdote"}
TIERS = {"A", "B", "C", "D", "E"}
GRADES = {"Strong", "Moderate", "Limited", "Excluded"}
RULE_IDS = {"R1", "R2", "R3", "R4", "R5", "R6"}
RATER_ROLES = {"user", "twin", "auditor", "physician", "nurse", "dietitian", "engineer", "public"}
RATING_FORMATS = {"thumbs", "stars5", "ten", "hundred", "text"}
WOULD_ACT = {"yes", "not_yet", "no", None}
SOURCE_TRUST_KEYS = {"doctor", "physician_creator", "coach", "reddit", "influencer"}


# ---------------------------------------------------------------- helpers

def _require(d: dict, keys: list[str], obj: str) -> None:
    if not isinstance(d, dict):
        raise ValueError(f"{obj}: expected object, got {type(d).__name__}")
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"{obj}: missing fields {missing}")


def _ordinal(value: Any, name: str, lo: int = 1, hi: int = 5) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
        raise ValueError(f"{name}: expected integer {lo} to {hi}, got {value!r}")


def _one_of(value: Any, allowed: set, name: str) -> None:
    if value not in allowed:
        raise ValueError(f"{name}: {value!r} not in {sorted(map(str, allowed))}")


def _str_list(value: Any, name: str) -> None:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"{name}: expected list of strings")


# ---------------------------------------------------------------- Persona

@dataclass
class Medication:
    name: str
    approved: bool


@dataclass
class SupplementPeptide:
    name: str
    source: str
    fda_approved: bool = False


@dataclass
class Persona:
    user_id: str
    goals: list[str]
    conditions: list[str]
    medications: list[Medication]
    supplements_peptides: list[SupplementPeptide]
    risk_tolerance: int
    readiness_to_act: int
    source_trust: dict[str, int]
    synthetic: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def validate_persona(d: dict) -> Persona:
    _require(d, ["user_id", "goals", "conditions", "medications", "supplements_peptides",
                 "risk_tolerance", "readiness_to_act", "source_trust"], "Persona")
    if d.get("synthetic") is not True:
        raise ValueError("Persona: synthetic must be true (synthetic personas only)")
    _str_list(d["goals"], "Persona.goals")
    _str_list(d["conditions"], "Persona.conditions")
    _ordinal(d["risk_tolerance"], "Persona.risk_tolerance")
    _ordinal(d["readiness_to_act"], "Persona.readiness_to_act")

    meds = []
    for i, m in enumerate(d["medications"]):
        _require(m, ["name", "approved"], f"Persona.medications[{i}]")
        if not isinstance(m["approved"], bool):
            raise ValueError(f"Persona.medications[{i}].approved: expected bool")
        meds.append(Medication(m["name"], m["approved"]))

    sups = []
    for i, s in enumerate(d["supplements_peptides"]):
        _require(s, ["name", "source"], f"Persona.supplements_peptides[{i}]")
        sups.append(SupplementPeptide(s["name"], s["source"], bool(s.get("fda_approved", False))))

    trust = d["source_trust"]
    if not isinstance(trust, dict) or set(trust) != SOURCE_TRUST_KEYS:
        raise ValueError(f"Persona.source_trust: keys must be exactly {sorted(SOURCE_TRUST_KEYS)}")
    for k, v in trust.items():
        _ordinal(v, f"Persona.source_trust.{k}")

    return Persona(d["user_id"], d["goals"], d["conditions"], meds, sups,
                   d["risk_tolerance"], d["readiness_to_act"], dict(trust), True)


# ---------------------------------------------------------------- Source

@dataclass
class Source:
    id: str
    lane: str
    title: str
    url: str | None
    speaker: str
    speaker_credential: str | None
    platform: str
    cites_evidence: bool
    coi: str
    text: str
    # Field the credential belongs to (e.g. "obesity medicine"), used by the
    # M2 classifier to flag out-of-field credentials. None if uncredentialed.
    credential_field: str | None = None
    # Public lane: the main claim of the post and the field it belongs to.
    # Expertise is judged per (speaker, claim), never per platform.
    claim: str | None = None
    claim_field: str | None = None
    # Clinical lane only: publication types from PubMed (drives tier A/B/C).
    publication_types: list[str] = field(default_factory=list)
    # Clinical lane only: full journal title and MEDLINE abbreviation (e.g. "N Engl J Med").
    journal: str | None = None
    journal_abbrev: str | None = None
    synthetic: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def validate_source(d: dict) -> Source:
    _require(d, ["id", "lane", "title", "url", "speaker", "speaker_credential",
                 "platform", "cites_evidence", "coi", "text"], "Source")
    _one_of(d["lane"], LANES, f"Source[{d['id']}].lane")
    _one_of(d["coi"], COI, f"Source[{d['id']}].coi")
    if not isinstance(d["cites_evidence"], bool):
        raise ValueError(f"Source[{d['id']}].cites_evidence: expected bool")
    if not d["text"].strip():
        raise ValueError(f"Source[{d['id']}].text: empty")
    return Source(
        id=d["id"], lane=d["lane"], title=d["title"], url=d["url"], speaker=d["speaker"],
        speaker_credential=d["speaker_credential"], platform=d["platform"],
        cites_evidence=d["cites_evidence"], coi=d["coi"], text=d["text"],
        credential_field=d.get("credential_field"),
        claim=d.get("claim"), claim_field=d.get("claim_field"),
        publication_types=list(d.get("publication_types", [])),
        journal=d.get("journal"), journal_abbrev=d.get("journal_abbrev"),
        synthetic=bool(d.get("synthetic", False)),
    )


# ---------------------------------------------------------------- M2+ objects

@dataclass
class ClassifiedSource:
    source: Source
    expert_category: str
    out_of_field: bool
    tier: str

    def __post_init__(self) -> None:
        _one_of(self.expert_category, EXPERT_CATEGORIES, "ClassifiedSource.expert_category")
        _one_of(self.tier, TIERS, "ClassifiedSource.tier")


@dataclass
class GradedClaim:
    claim: str
    sources: list[str]
    grade: str
    rule_id: str
    safety_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _one_of(self.grade, GRADES, "GradedClaim.grade")
        _one_of(self.rule_id, RULE_IDS, "GradedClaim.rule_id")


@dataclass
class PlanItem:
    action: str
    grade: str
    rule_id: str
    source_ids: list[str]
    pros: list[str]
    cons: list[str]


@dataclass
class Plan:
    immediate: list[PlanItem]
    next: list[PlanItem]
    longer_term: list[PlanItem]
    medical_vs_public: dict[str, list]


def validate_plan(d: dict) -> Plan:
    _require(d, ["immediate", "next", "longer_term", "medical_vs_public"], "Plan")
    horizons = {}
    for h in ("immediate", "next", "longer_term"):
        items = []
        for i, it in enumerate(d[h]):
            where = f"Plan.{h}[{i}]"
            _require(it, ["action", "grade", "rule_id", "source_ids", "pros", "cons"], where)
            _one_of(it["grade"], GRADES - {"Excluded"}, f"{where}.grade")
            _one_of(it["rule_id"], RULE_IDS, f"{where}.rule_id")
            if not it["source_ids"]:
                raise ValueError(f"{where}.source_ids: every recommendation needs a source")
            items.append(PlanItem(**{k: it[k] for k in PlanItem.__dataclass_fields__}))
        horizons[h] = items
    mvp = d["medical_vs_public"]
    _require(mvp, ["agree", "split"], "Plan.medical_vs_public")
    return Plan(horizons["immediate"], horizons["next"], horizons["longer_term"], mvp)


@dataclass
class Rating:
    response_id: str
    rater_id: str
    rater_role: str
    format: str
    raw: str
    score_0_1: float | None
    would_act: str | None
    dimensions: dict[str, int] = field(default_factory=dict)
    kordi_message_id: str | None = None

    def __post_init__(self) -> None:
        _one_of(self.rater_role, RATER_ROLES, "Rating.rater_role")
        _one_of(self.format, RATING_FORMATS, "Rating.format")
        _one_of(self.would_act, WOULD_ACT, "Rating.would_act")
        if self.score_0_1 is not None and not 0.0 <= self.score_0_1 <= 1.0:
            raise ValueError(f"Rating.score_0_1: {self.score_0_1} outside 0 to 1")
        for k, v in self.dimensions.items():
            _ordinal(v, f"Rating.dimensions.{k}", 0, 2)
