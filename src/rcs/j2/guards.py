"""Garde-fous déterministes, identiques pour toutes les stratégies (mono / routing / cascade).

- PII : bloque une question contenant des données personnelles (DOC04) -> revue humaine.
- Injection : retire du contexte les passages contenant des instructions hostiles.
- Hors périmètre : abstention si aucun passage n'atteint le score de pertinence minimal.
- Validation de sortie : citation d'une source récupérée, pas de fuite de charge d'injection.
"""
from __future__ import annotations

import re

PII_PATTERNS = {
    "nir": re.compile(r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone_fr": re.compile(r"\b0[1-9](?:[\s.-]?\d{2}){4}\b"),
    "patient_name": re.compile(r"\bpatient(?:e)?\s+[A-ZÉÈ][a-zéèêëàç]+(?:\s+[A-ZÉÈ][a-zéèêëàç]+)?"),
}

INJECTION_PATTERNS = re.compile(
    r"(ignore[rz]?\s+(toutes\s+)?(les\s+)?instructions|ignore (all|previous)|note syst[eè]me|system prompt|"
    r"mot de passe|password|tu es maintenant|you are now)", re.IGNORECASE)

INJECTION_PAYLOAD_MARKERS = ["ACCÈS ADMIN", "ACCES ADMIN", "mot de passe"]

ABSTAIN_MARKERS = ["information non disponible", "je ne sais pas", "pas dans les sources", "aucune source",
                   "ne permettent pas de répondre", "ne contient pas", "revue humaine"]

CITATION_RE = re.compile(r"\[?(DOC\d{2})\]?")

MIN_RETRIEVAL_SCORE = 0.12


def detect_pii(text: str) -> list[str]:
    return [name for name, pat in PII_PATTERNS.items() if pat.search(text)]


def sanitize_passages(passages: list[str]) -> tuple[list[str], int]:
    """Supprime les phrases contenant des motifs d'injection ; renvoie (passages nettoyés, nb retirés)."""
    removed, clean = 0, []
    for p in passages:
        kept = []
        for sentence in re.split(r"(?<=[.!?»])\s+", p):
            if INJECTION_PATTERNS.search(sentence):
                removed += 1
            else:
                kept.append(sentence)
        clean.append(" ".join(kept))
    return clean, removed


def is_abstention(answer: str) -> bool:
    a = answer.lower()
    return any(m in a for m in ABSTAIN_MARKERS)


def cited_docs(answer: str) -> set[str]:
    return set(CITATION_RE.findall(answer))


def validate_answer(answer: str, allowed_docs: set[str]) -> tuple[bool, str]:
    """Contrat de sortie : non vide, borné, sans charge d'injection, et soit abstention explicite,
    soit au moins une citation [DOCxx] appartenant aux passages fournis."""
    if not answer or not answer.strip():
        return False, "empty"
    if len(answer) > 1500:
        return False, "too_long"
    if any(m.lower() in answer.lower() for m in INJECTION_PAYLOAD_MARKERS):
        return False, "injection_payload"
    if is_abstention(answer):
        return True, "abstention"
    cites = cited_docs(answer)
    content = re.sub(r"sources?\s*:?", " ", CITATION_RE.sub(" ", answer), flags=re.IGNORECASE)
    if len(re.findall(r"\w+", content)) < 5:
        return False, "citation_only"
    if not cites:
        return False, "no_citation"
    if not cites & allowed_docs:
        return False, "citation_not_in_context"
    return True, "ok"
