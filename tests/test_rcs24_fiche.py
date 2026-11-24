"""RCS-24 — contrôle du livrable documentaire (sections attendues, statut des chiffres, pas de secret)."""
import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/22_rcs24_fiche_accessgudid.md"

NIR = re.compile(r"\b[12]\s?\d{2}\s?(0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}(\s?\d{2})?\b")
NAMED_PATIENT = re.compile(r"(?i)\bpatient(e)?\s+[A-Z][a-zé]+\s+[A-Z][a-zé]+")


def test_document_present_and_complete():
    text = DOC.read_text(encoding="utf-8")
    for needle in ['accessgudid.nlm.nih.gov', 'Device Lookup', 'GMDN', 'Utilité métier', 'absent']:
        assert needle in text, needle


def test_no_secret():
    text = DOC.read_text(encoding="utf-8").lower()
    for bad in ("api_key=", "sk-", "ghp_", "password="):
        assert bad not in text


def test_no_patient_identifier():
    """Ni NIR (numéro de sécurité sociale) ni nom de patient dans la fiche."""
    text = DOC.read_text(encoding="utf-8")
    assert not NIR.search(text)
    assert not NAMED_PATIENT.search(text)


def test_patient_identifier_patterns_detect_examples():
    """Les motifs ci-dessus détectent bien un NIR et un nom de patient (contrôle du contrôle)."""
    assert NIR.search("NIR 1 85 05 75 123 456 78")
    assert NAMED_PATIENT.search("Le patient Jean Dupont a eu un examen")
