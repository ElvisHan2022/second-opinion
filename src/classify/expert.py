"""Expert classifier (SPEC section 4): expertise is judged per claim, never by platform.

A credential counts only inside its field. A credential outside the claim's
field is flagged out_of_field and treated as no credential.
"""
from __future__ import annotations

from src.schemas import Source

# credential field -> claim fields it covers (every field also covers itself)
COVERAGE: dict[str, set[str]] = {
    "internal medicine": {"obesity medicine", "primary care"},
    "primary care": {"obesity medicine"},
    "obesity medicine": {"nutrition", "exercise science"},
    "sports medicine": {"exercise science"},
    # Ruling R11: a general medical credential covers medical claims.
    "medicine": {"obesity medicine", "pharmacology", "primary care", "sports medicine", "internal medicine"},
    "chiropractic": set(),
    "personal training": set(),
}


def covers(credential_field: str | None, claim_field: str | None) -> bool:
    if not credential_field or not claim_field:
        return False
    return credential_field == claim_field or claim_field in COVERAGE.get(credential_field, set())


def classify_expert(source: Source) -> tuple[str, bool]:
    """Return (expert_category, out_of_field). The platform is never read."""
    if source.lane == "clinical":
        return "expert_evidence", False
    has_credential = bool(source.speaker_credential)
    credentialed = has_credential and covers(source.credential_field, source.claim_field)
    out_of_field = has_credential and not credentialed
    if credentialed:
        category = "expert_evidence" if source.cites_evidence else "expert_opinion"
    else:
        category = "relayed_evidence" if source.cites_evidence else "anecdote"
    return category, out_of_field
