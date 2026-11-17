"""M3 structured response composer: two fixed-template sentences per claim topic."""
import re

import pytest

from src.respond.structured import (
    clinical_response,
    compose_all,
    extract_study_size,
    load_topics,
    public_response,
)
from src.retrieval.clinical import load_snapshot
from src.retrieval.public import REAL_POSTS, load_posts
from src.safety import DOSE_PATTERN, NON_APPROVED_PEPTIDES, redact_dosing
from src.schemas import Source

TOPIC_IDS = ["t-glp1-weightloss", "t-resistance", "t-protein", "t-leanmass", "t-bpc-muscle", "t-bpc-safety", "t-collagen"]


def _clinical(sid, abbrev, text, ptypes):
    return Source(id=sid, lane="clinical", title=f"title {sid}", url=None, speaker="A et al.",
                  speaker_credential="peer-reviewed publication", platform="PubMed",
                  cites_evidence=True, coi="unknown", text=text, publication_types=ptypes,
                  journal=abbrev, journal_abbrev=abbrev)


def _post(pid, platform, synthetic=True):
    return Source(id=pid, lane="public", title=pid, url=None, speaker="someone",
                  speaker_credential=None, platform=platform, cites_evidence=False,
                  coi="unknown", text="a post", synthetic=synthetic)


def _topic(stances):
    return {"id": "t-x", "topic": "x", "finding": "X", "recommendation": "Y",
            "public_conclusion": "Z", "stances": stances}


def _dosing_near_peptide(text):
    for m in DOSE_PATTERN.finditer(text):
        window = text[max(0, m.start() - 120): m.end() + 120].lower()
        if any(p.lower() in window for p in NON_APPROVED_PEPTIDES):
            return True
    return False


def test_weightloss_topic_tags_only_sources_on_glp1_efficacy():
    stances = {t["id"]: t for t in load_topics()}["t-glp1-weightloss"]["stances"]
    assert "pub-06" not in stances and "pmid-40914550" not in stances


# ------------------------------------------------------------- study size

def test_extract_study_size():
    assert extract_study_size("randomized 1,961 adults") == 1961
    assert extract_study_size("(n = 304)") == 304
    assert extract_study_size("N=12 and 2,539 participants") == 2539
    assert extract_study_size("a review of trials") is None
    assert extract_study_size("in 3 patients") is None


def test_extract_study_size_prefers_randomised_count():
    assert extract_study_size("Of 1,514 participants screened, 938 were randomly assigned.") == 938
    assert extract_study_size("1595 patients were screened, of whom 1210 were randomly assigned to "
                              "semaglutide (n=404) or placebo (n=403).") == 1210
    assert extract_study_size("of 1514 adults assessed for eligibility, 938 (mean age 54 years "
                              "[SD 10], 476 [51%] were female) were randomly assigned") == 938
    assert extract_study_size("We randomly assigned 304 adults (1:1) to drug or placebo; "
                              "2,000 people were contacted.") == 304
    assert extract_study_size("1,407 participants were randomised to the trial.") == 1407
    assert extract_study_size("A total of 751 participants underwent randomization.") == 751
    # Ratios after "randomly assigned" are not counts.
    assert extract_study_size("were randomly assigned 2:1 to drug; 120 adults enrolled") == 120


def test_extract_study_size_ignores_screened_numbers():
    assert extract_study_size("We screened 2,000 patients and enrolled 160 patients.") == 160


def test_real_trial_sizes_are_randomised_counts():
    by_id = {s.id: s for s in load_snapshot()}
    assert extract_study_size(by_id["pmid-37385275"].text) == 938   # SURMOUNT-2
    assert extract_study_size(by_id["pmid-33667417"].text) == 1210  # STEP 2
    assert extract_study_size(by_id["pmid-37385278"].text) == 667   # OASIS 1


def test_extract_study_size_thin_space_thousands():
    # PubMed abstracts sometimes use a thin space as the thousands separator.
    assert extract_study_size("Twenty RCTs comprising 15\u2009782 participants") == 15782


# ------------------------------------------------------------- templates

def test_clinical_template_exact():
    obesity = _clinical("s-ob", "Obesity", "A review of trials.", ["Journal Article", "Review"])
    nejm = _clinical("s-nejm", "N Engl J Med", "We randomized 1,961 adults.",
                     ["Journal Article", "Randomized Controlled Trial"])
    res = clinical_response(_topic({"s-ob": "cautions", "s-nejm": "supports"}), [obesity, nejm])
    assert res["text"] == ("From NEJM and Obesity sources (most reputable), we identified 2 studies "
                           "with study sizes of 1,961 and size not reported, with the main finding "
                           "that X. Thus, we recommend Y.")
    assert res["n_studies"] == 2
    assert res["study_sizes"] == [1961, None]
    assert res["sources"] == ["s-nejm", "s-ob"]
    assert res["redacted"] is False


def test_clinical_skips_opposes_and_untagged():
    a = _clinical("a", "Obesity", "120 adults", ["Review"])
    b = _clinical("b", "Obesity", "300 adults", ["Review"])
    c = _clinical("c", "Obesity", "400 adults", ["Review"])
    res = clinical_response(_topic({"a": "supports", "b": "opposes"}), [a, b, c])
    assert res["sources"] == ["a"]
    assert res["n_studies"] == 1


def test_clinical_journal_names_distinct_capped_and_ordered():
    srcs = [
        _clinical("o1", "Obes Rev", "x", ["Review"]),
        _clinical("d1", "Diabetes Care", "x", ["Review"]),
        _clinical("m1", "Diabetes Obes Metab", "x", ["Meta-Analysis"]),
        _clinical("l1", "Lancet Diabetes Endocrinol", "x", ["Randomized Controlled Trial"]),
        _clinical("l2", "Lancet", "x", ["Randomized Controlled Trial"]),
    ]
    res = clinical_response(_topic({s.id: "supports" for s in srcs}), srcs)
    # Lancet family collapses to one "Lancet"; tier-A/B journal before reviews; at most 3 names.
    assert res["text"].startswith("From Lancet, Diabetes Obes Metab and Diabetes Care sources")
    assert res["n_studies"] == 5


def test_long_size_lists_are_compacted():
    texts = ["We randomized 1,961 adults.", "We enrolled 160 patients.", "x", "We enrolled 12,000 adults.",
             "We enrolled 300 adults.", "x"]
    srcs = [_clinical(f"s{i}", "Obesity", t, ["Randomized Controlled Trial"]) for i, t in enumerate(texts)]
    res = clinical_response(_topic({s.id: "supports" for s in srcs}), srcs)
    assert ("with study sizes of 4 reported sizes from 160 to 12,000 and 2 not reported, "
            "with the main finding") in res["text"]
    assert res["study_sizes"] == [1961, 160, None, 12000, 300, None]
    # Four or fewer keep the list.
    res4 = clinical_response(_topic({s.id: "supports" for s in srcs[:4]}), srcs[:4])
    assert "study sizes of 1,961, 160, size not reported and 12,000," in res4["text"]
    # More than four, all reported: no "not reported" suffix.
    full = [s for s in srcs if s.text != "x"] + [_clinical("s9", "Obesity", "We enrolled 50 adults.", [])]
    res5 = clinical_response(_topic({s.id: "supports" for s in full}), full)
    assert "study sizes of 5 reported sizes from 50 to 12,000, with" in res5["text"]


def test_public_template_exact():
    posts = [_post("p1", "Reddit"), _post("p2", "TikTok"), _post("p3", "Instagram")]
    res = public_response(_topic({"p1": "supports", "p2": "supports", "p3": "opposes"}), posts)
    assert res["text"] == ("Across Reddit, TikTok and Instagram, we identified 2 posts supporting "
                           "the conclusion that Z. 1 post disputed it.")
    assert (res["n_support"], res["n_oppose"]) == (2, 1)
    assert res["platforms"] == ["Reddit", "TikTok", "Instagram"]


def test_public_no_disputed_clause_when_no_opposition():
    posts = [_post("p1", "Reddit"), _post("p2", "Reddit")]
    res = public_response(_topic({"p1": "supports", "p2": "supports"}), posts)
    assert res["text"] == "Across Reddit, we identified 2 posts supporting the conclusion that Z."


def test_public_cautions_not_counted():
    posts = [_post("p1", "Reddit"), _post("p2", "X")]
    res = public_response(_topic({"p1": "supports", "p2": "cautions"}), posts)
    assert (res["n_support"], res["n_oppose"], res["n_synthetic"]) == (1, 0, 1)
    assert res["platforms"] == ["Reddit"]
    assert res["text"] == "Across Reddit, we identified 1 post supporting the conclusion that Z."


def test_narrative_review_size_not_reported():
    narrative = _clinical("nr", "Obes Rev", "Trials enrolled 1,961 adults.", ["Journal Article", "Review"])
    sr = _clinical("sr", "Obes Rev", "Pooled 2,000 participants.", ["Review", "Systematic Review"])
    ma = _clinical("ma", "Obes Rev", "Pooled 3,000 participants.", ["Meta-Analysis"])
    rct = _clinical("rct", "Obes Rev", "We randomized 400 adults.", ["Randomized Controlled Trial"])
    srcs = [narrative, sr, ma, rct]
    res = clinical_response(_topic({s.id: "supports" for s in srcs}), srcs)
    sizes = dict(zip(res["sources"], res["study_sizes"]))
    assert sizes == {"nr": None, "sr": 2000, "ma": 3000, "rct": 400}


def test_singular_words():
    one = _clinical("s1", "Obesity", "We enrolled 50 adults.", ["Review"])
    res = clinical_response(_topic({"s1": "supports"}), [one])
    assert " 1 study with " in res["text"]
    pub = public_response(_topic({"p1": "supports"}), [_post("p1", "Reddit")])
    assert " 1 post supporting " in pub["text"]


def test_zero_matches_fall_back_to_plain_sentences():
    res = clinical_response(_topic({}), [_clinical("s1", "Obesity", "x", ["Review"])])
    assert res["n_studies"] == 0
    # No source, no recommendation.
    assert res["text"] == "We identified no studies in our clinical sources that test this claim."
    assert res["recommendation"] is None and res["finding"] is None
    pub = public_response(_topic({}), [_post("p1", "Reddit")])
    assert pub["n_support"] == pub["n_oppose"] == 0
    assert "Across ," not in pub["text"]


def test_public_counts_synthetic_posts():
    posts = [_post("p1", "Reddit"), _post("p2", "TikTok", synthetic=False),
             _post("p3", "X"), _post("p4", "X")]  # p4 untagged: not counted
    res = public_response(_topic({"p1": "supports", "p2": "supports", "p3": "opposes"}), posts)
    assert res["n_synthetic"] == 2
    for topic in compose_all():
        assert topic["public"]["n_synthetic"] == 0, topic["topic_id"]  # the demo lane is real posts


# ------------------------------------------------------------- fixture + safety

def test_topics_fixture_ids_and_stance_targets():
    topics = load_topics()
    assert [t["id"] for t in topics] == TOPIC_IDS
    known = {s.id for s in load_snapshot()} | {p.id for p in load_posts(REAL_POSTS)}
    for t in topics:
        assert set(t["stances"]) <= known, f"{t['id']} tags unknown source ids"
        assert not any(sid.startswith("pub-") for sid in t["stances"]), f"{t['id']} still tags synthetic posts"
        assert set(t["stances"].values()) <= {"supports", "opposes", "cautions"}
        for field in ("finding", "recommendation"):
            assert t[field][0].islower() and not t[field].endswith("."), (t["id"], field)


def test_recommendations_never_contain_peptide_dosing():
    for topic in compose_all():
        for lane in ("clinical", "public"):
            assert not _dosing_near_peptide(topic[lane]["text"]), (topic["topic_id"], lane)
        assert not DOSE_PATTERN.search(topic["clinical"]["recommendation"] or "")


def test_weightloss_topic_cites_nejm_and_lancet():
    by_id = {t["topic_id"]: t for t in compose_all()}
    assert by_id["t-glp1-weightloss"]["clinical"]["text"].startswith("From NEJM, Lancet and ")


def test_collagen_has_no_unsourced_recommendation():
    clin = {t["topic_id"]: t for t in compose_all()}["t-collagen"]["clinical"]
    assert clin["n_studies"] == 0 and clin["recommendation"] is None
    assert "recommend" not in clin["text"]


def test_bpc_topic_refers_to_clinician():
    by_id = {t["topic_id"]: t for t in compose_all()}
    for tid in ("t-bpc-muscle", "t-bpc-safety"):
        text = by_id[tid]["clinical"]["text"]
        assert "clinician" in text or "prescriber" in text, tid
        assert "not FDA-approved" in text, tid


def test_resistance_supported_by_medicine_and_public():
    t = {t["topic_id"]: t for t in compose_all()}["t-resistance"]
    assert t["clinical"]["n_studies"] >= 1
    assert t["public"]["n_support"] > 0 and t["public"]["n_oppose"] == 0


def test_bpc_muscle_public_side_leans_supportive():
    pub = {t["topic_id"]: t for t in compose_all()}["t-bpc-muscle"]["public"]
    assert pub["n_support"] > pub["n_oppose"] > 0


def test_topics_without_real_posts_use_public_fallback():
    by_id = {t["topic_id"]: t for t in compose_all()}
    for tid in ("t-glp1-weightloss", "t-collagen"):
        assert by_id[tid]["public"]["text"].startswith("We identified no public posts"), tid


def test_redact_dosing():
    out, flag = redact_dosing("Some use BPC-157 at 250 mcg daily. Lift weights.")
    assert flag is True
    assert "250" not in out and "BPC-157" not in out
    assert "[removed: dosing for a non-approved peptide]" in out
    assert out.endswith("Lift weights.")
    assert redact_dosing("Semaglutide 2.4 mg weekly.") == ("Semaglutide 2.4 mg weekly.", False)


def test_redact_dosing_peptide_spelling_variants():
    out, flag = redact_dosing("BPC157 was injected at 500mcg. Rest days matter.")
    assert flag is True and out.endswith("Rest days matter.")


@pytest.mark.parametrize("dose", ["250 milligrams", "5 micrograms", "1 microgram", "0.5 mL", "2 cc",
                                  "10 milligram"])
def test_redact_dosing_spelled_out_and_volume_units(dose):
    out, flag = redact_dosing(f"Inject BPC-157 at {dose} twice a day. Lift weights.")
    assert flag is True, dose
    assert dose not in out and out.endswith("Lift weights.")


def test_redact_dosing_body_protection_compound():
    out, flag = redact_dosing("Body Protection Compound is taken at 300 mcg. Sleep well.")
    assert flag is True and out.endswith("Sleep well.")
    out, flag = redact_dosing("the body protection compound, 2 mL per day.")
    assert flag is True


def test_redact_dosing_leaves_approved_drug_doses():
    for text in ("Semaglutide 2.4 mg weekly.", "Semaglutide 2.4 milligrams weekly in 0.75 mL.",
                 "Inject 1 mL of tirzepatide."):
        assert redact_dosing(text) == (text, False)


def test_composer_redacts_and_flags():
    topic = _topic({"s1": "supports"})
    topic["finding"] = "people take BPC-157 at 250 mcg"
    topic["recommendation"] = "BPC-157 at 2 milligrams daily"
    res = clinical_response(topic, [_clinical("s1", "Obesity", "x", ["Review"])])
    assert res["redacted"] is True
    for field in ("text", "finding", "recommendation"):
        assert "250 mcg" not in res[field] and "2 milligrams" not in res[field], field
    assert res["finding"] == res["recommendation"] == "[removed: dosing for a non-approved peptide]"

    pub_topic = _topic({"p1": "supports"})
    pub_topic["public_conclusion"] = "BPC-157 at 500 mcg protects muscle"
    pub = public_response(pub_topic, [_post("p1", "Reddit")])
    assert pub["redacted"] is True
    assert "500 mcg" not in pub["public_conclusion"] and "500 mcg" not in pub["text"]


def test_composer_not_flagged_without_dosing():
    res = clinical_response(_topic({"s1": "supports"}), [_clinical("s1", "Obesity", "x", ["Review"])])
    pub = public_response(_topic({"p1": "supports"}), [_post("p1", "Reddit")])
    assert res["redacted"] is False and pub["redacted"] is False


def test_compose_all_shape():
    out = compose_all()
    assert [t["topic_id"] for t in out] == TOPIC_IDS
    for t in out:
        assert t["topic"]
        assert t["clinical"]["text"] and t["public"]["text"]
        assert t["clinical"]["topic_id"] == t["public"]["topic_id"] == t["topic_id"]
        assert len(t["clinical"]["study_sizes"]) == t["clinical"]["n_studies"]
