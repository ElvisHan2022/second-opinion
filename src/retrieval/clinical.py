"""Clinical lane: PubMed E-utilities search, cached (SPEC section 4).

esearch -> efetch (XML) for titles, abstracts and publication types.
Every HTTP response is cached under data/cache/ (gitignored). Because the
cache is not committed, `snapshot()` also writes the parsed Sources to
data/fixtures/clinical_sources.json so teammates and the demo run offline.

medRxiv is not wired in: its public API has no keyword search, only date
and DOI lookups. Listed as a follow-up.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from src.schemas import Source, validate_source

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache" / "pubmed"
SNAPSHOT = ROOT / "data" / "fixtures" / "clinical_sources.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Demo question: avoiding muscle loss on semaglutide, and whether to add BPC-157.
DEMO_QUERIES = {
    "glp1_lean_mass": '(semaglutide OR tirzepatide OR "GLP-1 receptor agonist") AND ("lean mass" OR "fat-free mass" OR "muscle mass")',
    "exercise_protein_glp1": '("GLP-1 receptor agonist" OR semaglutide OR liraglutide) AND ("resistance training" OR exercise OR "protein intake") AND (muscle OR "lean mass")',
    "nejm_lancet": '("lean mass" OR "fat-free mass" OR "muscle mass" OR "resistance training" OR exercise) AND '
                   '("N Engl J Med"[ta] OR "Lancet"[ta] OR "Lancet Diabetes Endocrinol"[ta])',
    "bpc157": '"BPC-157" OR "BPC 157" OR "body protection compound"',
}
PER_QUERY = 5


def _get(url: str, params: dict) -> str:
    params = {**params, "tool": "credence-hackathon"}
    if os.getenv("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    if os.getenv("NCBI_EMAIL"):
        params["email"] = os.environ["NCBI_EMAIL"]
    cache_params = {k: v for k, v in params.items() if k not in ("api_key", "email")}
    key = hashlib.sha256(f"{url}?{urllib.parse.urlencode(sorted(cache_params.items()))}".encode()).hexdigest()[:24]
    path = CACHE / f"{key}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    full = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(full, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    time.sleep(0.4)  # stay under 3 requests per second without an API key
    return body


def esearch(term: str, retmax: int = PER_QUERY) -> list[str]:
    body = _get(f"{EUTILS}/esearch.fcgi", {"db": "pubmed", "term": term, "retmax": retmax,
                                           "sort": "relevance", "retmode": "json"})
    return json.loads(body)["esearchresult"]["idlist"]


def efetch(pmids: list[str]) -> list[Source]:
    if not pmids:
        return []
    body = _get(f"{EUTILS}/efetch.fcgi", {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    out = []
    for art in ET.fromstring(body).iter("PubmedArticle"):
        pmid = art.findtext(".//PMID")
        title = "".join(art.find(".//ArticleTitle").itertext()).strip()
        abstract = " ".join("".join(t.itertext()).strip() for t in art.findall(".//Abstract/AbstractText"))
        journal = art.findtext(".//Journal/Title") or "PubMed"
        journal_abbrev = art.findtext(".//MedlineJournalInfo/MedlineTA") or art.findtext(".//Journal/ISOAbbreviation")
        year = art.findtext(".//PubDate/Year") or (art.findtext(".//PubDate/MedlineDate") or "")[:4]
        authors = art.findall(".//AuthorList/Author")
        first = authors[0].findtext("LastName") if authors else None
        speaker = f"{first} et al." if first and len(authors) > 1 else (first or "Unknown")
        ptypes = [p.text for p in art.findall(".//PublicationTypeList/PublicationType") if p.text]
        out.append(validate_source({
            "id": f"pmid-{pmid}",
            "lane": "clinical",
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "speaker": f"{speaker} ({journal}, {year})",
            "speaker_credential": "peer-reviewed publication",
            "credential_field": "biomedical research",
            "platform": "PubMed",
            "cites_evidence": True,
            "coi": "unknown",
            "text": abstract or title,
            "publication_types": ptypes,
            "journal": journal,
            "journal_abbrev": journal_abbrev,
        }))
    return out


def journal_badge(source: Source) -> str:
    """UI badge from the MEDLINE journal abbreviation: NEJM, Lancet, else PubMed."""
    abbrev = source.journal_abbrev or ""
    if abbrev == "N Engl J Med":
        return "NEJM"
    if abbrev.startswith("Lancet"):
        return "Lancet"
    return "PubMed"


def search(queries: dict[str, str] = DEMO_QUERIES) -> list[Source]:
    """Run every query, dedupe by PMID, keep first-seen order."""
    seen, sources = set(), []
    for term in queries.values():
        for s in efetch(esearch(term)):
            if s.id not in seen:
                seen.add(s.id)
                sources.append(s)
    return sources


def snapshot(sources: list[Source]) -> Path:
    SNAPSHOT.write_text(json.dumps({"queries": DEMO_QUERIES, "sources": [s.to_dict() for s in sources]},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return SNAPSHOT


def load_snapshot() -> list[Source]:
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return [validate_source(s) for s in data["sources"]]


if __name__ == "__main__":
    srcs = search()
    print(f"{len(srcs)} sources -> {snapshot(srcs)}")
    for s in srcs:
        print(f"  {s.id}  {s.publication_types}  {s.title[:90]}")
