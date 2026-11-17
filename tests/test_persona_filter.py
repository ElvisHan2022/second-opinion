"""Task 3b: persona-aware clinical evidence (no diabetes -> drop type 2 diabetes trials)."""
import dataclasses

from src.intake.persona import load_persona, load_transcript
from src.respond.structured import compose_all, persona_filter
from src.retrieval.clinical import load_snapshot
from src.safety import DOSE_PATTERN

STEP_1, STEP_2 = "pmid-33567185", "pmid-33667417"
SURMOUNT_1, SURMOUNT_2 = "pmid-39536238", "pmid-37385275"
REASON = "type 2 diabetes population; persona has no diabetes"


def _ids(sources):
    return {s.id for s in sources}


def test_p002_is_the_synthetic_script_persona():
    p = load_persona("p-002")
    assert p.synthetic is True and p.user_id == "p-002"
    assert [m.name for m in p.medications] == ["semaglutide"]
    assert not any("diabetes" in c.lower() for c in p.conditions)
    assert any(s.name == "BPC-157" and not s.fda_approved for s in p.supplements_peptides)
    assert (p.risk_tolerance, p.readiness_to_act) == (3, 3)
    assert p.source_trust == {"doctor": 4, "physician_creator": 4, "coach": 3, "reddit": 3, "influencer": 2}
    transcript = load_transcript("p-002")
    assert transcript.startswith("# SYNTHETIC intake transcript")
    assert not DOSE_PATTERN.search(transcript)


def test_p002_excludes_type2_diabetes_trials():
    kept, excluded = persona_filter(load_snapshot(), load_persona("p-002"))
    assert {STEP_2, SURMOUNT_2} <= {e["id"] for e in excluded}
    assert {STEP_1, SURMOUNT_1} <= _ids(kept)
    assert not {STEP_2, SURMOUNT_2} & _ids(kept)
    for e in excluded:
        assert set(e) == {"id", "title", "reason"}
        assert e["reason"] == REASON
        assert "type 2 diabetes" in e["title"].lower()


def test_persona_with_type2_diabetes_excludes_nothing():
    p = dataclasses.replace(load_persona("p-002"), conditions=["obesity", "type 2 diabetes"])
    sources = load_snapshot()
    kept, excluded = persona_filter(sources, p)
    assert excluded == [] and _ids(kept) == _ids(sources)


def test_prediabetes_does_not_count_as_diabetes():
    p = load_persona("p-001")  # prediabetes only
    _, excluded = persona_filter(load_snapshot(), p)
    assert STEP_2 in {e["id"] for e in excluded}


def test_diabetes_prevention_and_without_diabetes_titles_are_kept():
    sources = load_snapshot()
    by_id = {s.id: s for s in sources}
    assert "diabetes prevention" in by_id[SURMOUNT_1].title.lower()
    p = load_persona("p-002")
    prevention = dataclasses.replace(by_id[SURMOUNT_1], id="x-prev",
                                     title="Tirzepatide for Obesity and Type 2 Diabetes Prevention")
    without = dataclasses.replace(by_id[STEP_1], id="x-without",
                                  title="Semaglutide in adults without diabetes, versus type 2 diabetes cohorts")
    kept, _ = persona_filter([by_id[SURMOUNT_1], prevention, without], p)
    assert _ids(kept) == {SURMOUNT_1, "x-prev", "x-without"}


def test_weightloss_topic_lists_excluded_trials_for_p002():
    by_id = {t["topic_id"]: t for t in compose_all(persona=load_persona("p-002"))}
    wl = by_id["t-glp1-weightloss"]
    assert {e["id"] for e in wl["excluded_for_persona"]} == {STEP_2, SURMOUNT_2}
    assert not {STEP_2, SURMOUNT_2} & set(wl["clinical"]["sources"])
    assert "NEJM" in wl["clinical"]["text"]
    # Other topics tag no type 2 diabetes trial.
    for tid, t in by_id.items():
        if tid != "t-glp1-weightloss":
            assert t["excluded_for_persona"] == [], tid


def test_default_persona_is_p002():
    assert compose_all() == compose_all(persona=load_persona("p-002"))
