"""M2 expert classifier: per-claim expertise, never by platform."""
import dataclasses

from src.classify.expert import classify_expert, covers
from src.retrieval.clinical import load_snapshot
from src.retrieval.public import load_posts


def _post(pid):
    return next(p for p in load_posts() if p.id == pid)


def test_four_categories_from_fixture():
    assert classify_expert(_post("pub-01")) == ("expert_evidence", False)
    assert classify_expert(_post("pub-02")) == ("expert_opinion", False)
    assert classify_expert(_post("pub-08")) == ("relayed_evidence", False)
    assert classify_expert(_post("pub-07")) == ("anecdote", False)


def test_out_of_field_flagged():
    assert classify_expert(_post("pub-04")) == ("relayed_evidence", True)
    assert classify_expert(_post("pub-05"))[1] is True


def test_platform_independence():
    pub_01 = _post("pub-01")
    base = classify_expert(pub_01)
    for p in ("YouTube", "journal", "TikTok"):
        assert classify_expert(dataclasses.replace(pub_01, platform=p)) == base


def test_unknown_fields_are_out_of_field():
    src = dataclasses.replace(_post("pub-01"), speaker_credential="MD",
                              credential_field="dermatology", claim_field=None)
    category, out = classify_expert(src)
    assert out is True
    assert category in {"relayed_evidence", "anecdote"}


def test_covers_coverage_map():
    assert covers("obesity medicine", "obesity medicine")
    assert covers("internal medicine", "obesity medicine")
    assert not covers("obesity medicine", "internal medicine")
    assert not covers("chiropractic", "pharmacology")
    assert not covers(None, "obesity medicine")
    assert not covers("obesity medicine", None)


def test_clinical_sources_are_expert_evidence():
    sources = load_snapshot()
    assert sources
    for s in sources:
        assert classify_expert(s) == ("expert_evidence", False)
