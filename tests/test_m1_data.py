"""M1 data checks: persona, public posts, cached clinical sources."""
import json
import re

import pytest

from src.intake.persona import FIXTURES, extract_persona, load_persona, load_transcript
from src.retrieval import clinical
from src.retrieval.clinical import SNAPSHOT, journal_badge, load_snapshot
from src.retrieval.public import POSTS, load_posts
from src.schemas import Source, validate_persona

NON_APPROVED_PEPTIDES = ["BPC-157", "BPC 157", "TB-500", "ipamorelin", "CJC-1295"]
DOSE = re.compile(r"\d+(\.\d+)?\s*(mg|mcg|µg|μg|ug|units?|iu)\b", re.I)


# ------------------------------------------------------------- persona

def test_persona_fixture_validates_and_is_synthetic():
    p = load_persona("p-001")
    assert p.synthetic is True
    assert {m.name for m in p.medications} == {"semaglutide", "metformin"}
    assert any(s.name == "BPC-157" and not s.fda_approved for s in p.supplements_peptides), \
        "demo persona must carry a non-approved peptide so R5 fires"
    assert 1 <= p.risk_tolerance <= 5 and 1 <= p.readiness_to_act <= 5


def test_persona_transcript_is_marked_synthetic():
    assert load_transcript("p-001").startswith("# SYNTHETIC")


def _persona_dict():
    return json.loads((FIXTURES / "p-001.json").read_text(encoding="utf-8"))


def test_persona_rejects_non_synthetic():
    d = _persona_dict()
    d["synthetic"] = False
    with pytest.raises(ValueError, match="synthetic"):
        validate_persona(d)


@pytest.mark.parametrize("field,value", [("risk_tolerance", 0), ("risk_tolerance", 6), ("readiness_to_act", "4")])
def test_persona_rejects_bad_ordinals(field, value):
    d = _persona_dict()
    d[field] = value
    with pytest.raises(ValueError, match=field):
        validate_persona(d)


def test_extract_persona_validates_llm_json_including_code_fence():
    fixture = (FIXTURES / "p-001.json").read_text(encoding="utf-8")
    p = extract_persona("transcript", "p-001", llm=lambda _prompt: f"```json\n{fixture}\n```")
    assert p.user_id == "p-001"
    with pytest.raises(ValueError):
        extract_persona("transcript", "p-001", llm=lambda _prompt: '{"user_id": "p-001"}')


# ------------------------------------------------------------- public lane

def test_public_posts_count_and_mix():
    posts = load_posts()
    assert 10 <= len(posts) <= 20
    assert {"Reddit", "X", "Instagram", "TikTok"} <= {p.platform for p in posts}
    creds = [p.speaker_credential or "" for p in posts]
    assert any("MD" in c for c in creds), "need a credentialed physician creator"
    assert any("trainer" in c for c in creds), "need a coach"
    assert any(p.speaker_credential is None and p.coi == "yes" for p in posts), "need an influencer with COI"


def test_public_posts_cover_all_four_expert_categories_inputs():
    """Each cell of the SPEC classifier table has at least one post (M2 will classify)."""
    posts = load_posts()
    in_field = lambda p: p.speaker_credential is not None and p.credential_field == p.claim_field
    cells = {(in_field(p), p.cites_evidence) for p in posts}
    assert cells == {(True, True), (True, False), (False, True), (False, False)}


def test_public_posts_include_out_of_field_credential():
    posts = load_posts()
    assert any(p.speaker_credential and p.credential_field != p.claim_field for p in posts)


def test_public_posts_are_flagged_synthetic_until_replaced():
    data = json.loads(POSTS.read_text(encoding="utf-8"))
    assert all(p["synthetic"] is True and p["url"] is None for p in data["posts"])


# ------------------------------------------------------------- clinical lane

def test_clinical_snapshot_has_cached_pubmed_sources():
    sources = load_snapshot()
    assert len(sources) >= 5
    for s in sources:
        assert s.lane == "clinical"
        assert re.fullmatch(r"pmid-\d+", s.id)
        assert s.url == f"https://pubmed.ncbi.nlm.nih.gov/{s.id[5:]}/"
    ptypes = {t for s in sources for t in s.publication_types}
    assert ptypes & {"Randomized Controlled Trial", "Systematic Review", "Meta-Analysis"}, \
        "need at least one Tier A candidate"


def test_clinical_snapshot_covers_bpc157():
    assert any("BPC" in s.title for s in load_snapshot())


def test_snapshot_includes_nejm_and_lancet():
    badges = {journal_badge(s) for s in load_snapshot()}
    assert {"NEJM", "Lancet"} <= badges


def test_clinical_sources_have_journal_fields():
    for s in load_snapshot():
        assert s.journal and s.journal_abbrev, s.id


@pytest.mark.parametrize("abbrev,badge", [
    ("N Engl J Med", "NEJM"),
    ("Lancet Diabetes Endocrinol", "Lancet"),
    ("Lancet", "Lancet"),
    ("Obesity (Silver Spring)", "PubMed"),
    (None, "PubMed"),
])
def test_journal_badge(abbrev, badge):
    src = Source(id="x", lane="clinical", title="t", url=None, speaker="s", speaker_credential=None,
                 platform="PubMed", cites_evidence=True, coi="unknown", text="t", journal_abbrev=abbrev)
    assert journal_badge(src) == badge


def test_efetch_empty_makes_no_request(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call")
    monkeypatch.setattr(clinical, "_get", boom)
    assert clinical.efetch([]) == []


# ------------------------------------------------------------- safety

@pytest.mark.parametrize("path", [
    POSTS, SNAPSHOT, FIXTURES / "p-001.json", FIXTURES / "p-001_transcript.txt",
], ids=lambda p: p.name)
def test_no_dosing_near_non_approved_peptides_in_fixtures(path):
    text = path.read_text(encoding="utf-8")
    for name in NON_APPROVED_PEPTIDES:
        for m in re.finditer(re.escape(name), text, re.I):
            window = text[max(0, m.start() - 120): m.end() + 120]
            assert not DOSE.search(window), f"dosing pattern near {name} in {path.name}: {window!r}"
