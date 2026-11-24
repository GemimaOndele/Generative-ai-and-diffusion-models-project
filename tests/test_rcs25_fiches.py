"""RCS-25 — contrôle du livrable documentaire (sections attendues, statut des chiffres, pas de secret)."""
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/23_rcs25_fiches_ai4i_mimii.md"


def test_document_present_and_complete():
    text = DOC.read_text(encoding="utf-8")
    for needle in ['CC BY 4.0', 'CC BY-NC-SA 4.0', 'non médicaux', 'Écart vs machine médicale réelle']:
        assert needle in text, needle


def test_no_secret_or_patient_identifier():
    text = DOC.read_text(encoding="utf-8").lower()
    for bad in ("api_key=", "sk-", "ghp_", "password="):
        assert bad not in text
