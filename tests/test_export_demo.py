import json
import re

from src import export_demo
from src.export_demo import build_demo_data, corner, topic_verdict, write_demo_js
from src.retrieval import public
from src.safety import DOSE_PATTERN, PEPTIDE_PATTERN

PROBLEM = ("People on GLP-1s get conflicting advice from doctors, influencers, and Reddit. "
           "Second Opinion shows what the clinical evidence says, what real users say, and how much "
           "weight each claim deserves.")


def test_corner_follows_classification_not_platform():
    real = {p.id: p for p in public.load_posts(public.REAL_POSTS)}
    for pid in ("real-15", "real-16"):  # credentialed, Instagram
        assert corner(export_demo.classify_expert(real[pid])[0]) == "medicine"
    assert corner(export_demo.classify_expert(real["real-02"])[0]) == "public"  # Reddit user
    synth = {p.id: p for p in public.load_posts()}
    assert corner(export_demo.classify_expert(synth["pub-04"])[0]) == "public"  # chiropractor


def test_topic_verdicts():
    data = build_demo_data()
    verdicts = {t["id"]: t["verdict"] for t in data["topics"]}
    assert verdicts["t-resistance"] == "agree"
    assert verdicts["t-bpc-muscle"] == "split"


def test_demo_js_escapes_script_close(tmp_path, monkeypatch):
    real_build = export_demo.build_demo_data

    def patched():
        d = real_build()
        d["fighters"][0]["claim"] = "x </script><b>"
        return d

    monkeypatch.setattr(export_demo, "build_demo_data", patched)
    out = write_demo_js(tmp_path / "demo_data.js")
    raw = out.read_text(encoding="utf-8")
    assert "</script>" not in raw and "</" not in raw
    assert raw.startswith("window.DEMO = ") and raw.rstrip().endswith(";")
    payload = json.loads(raw[len("window.DEMO = "):].rstrip().rstrip(";"))
    assert payload["fighters"][0]["claim"] == "x </script><b>"


def test_build_demo_data_shape():
    d = build_demo_data()
    assert d["product"] == "Second Opinion" and d["synthetic"] is True
    assert d["problem"] == PROBLEM
    assert "type 2 diabetes" in d["persona_note"]
    f = d["fighters"]
    assert d["counts"]["medicine"] + d["counts"]["public"] == len(f)
    assert {x["corner"] for x in f} <= {"medicine", "public"}
    assert {x["badge"] for x in f} & {"NEJM", "Lancet"}
    assert not any(x["synthetic"] for x in f)
    excluded = {e["id"] for e in d["excluded_for_persona"]}
    assert excluded and not excluded & {x["id"] for x in f}
    for t in d["topics"]:
        assert t["clinical"]["text"] and t["public"]["text"]
    for x in f:
        if x["lane"] == "public" and x["credential"]:
            assert x["credential_verified"] is False
        assert x["claim"] and x["title"] is not None


def test_no_peptide_dosing_in_export():
    blob = json.dumps(build_demo_data(), ensure_ascii=False)
    for m in DOSE_PATTERN.finditer(blob):
        window = blob[max(0, m.start() - 120): m.end() + 120]
        assert not PEPTIDE_PATTERN.search(window), window
