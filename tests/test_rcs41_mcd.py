"""RCS-41 — contrôle du livrable documentaire (sections attendues, statut des chiffres, pas de secret)."""
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/25_rcs41_mcd.md"


def test_document_present_and_complete():
    text = DOC.read_text(encoding="utf-8")
    for needle in ['RG1', 'RG10', '(0,n)', '(1,1)', 'JMerise']:
        assert needle in text, needle


def test_jmerise_export_present_and_valid():
    """Le MCD JMerise (.mcd, sérialisation Java) et son export PNG sont versionnés et référencés."""
    root = Path(__file__).resolve().parents[1] / "docs" / "jmerise"
    mcd = (root / "RCS41_MCD_RoboCare.mcd").read_bytes()
    png = (root / "RCS41_MCD_RoboCare.png").read_bytes()
    assert mcd[:4] == b"\xac\xed\x00\x05"          # en-tête de sérialisation Java (format JMerise)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    for name in ("SOURCE_DONNEES", "EXPERIMENT_METRIC", "EVALUE", "DECIDE"):
        assert name.encode() in mcd, name
    text = DOC.read_text(encoding="utf-8")
    assert "jmerise/RCS41_MCD_RoboCare.png" in text and "MESURE_RUN  (1,1)" not in text


def test_no_secret_or_patient_identifier():
    text = DOC.read_text(encoding="utf-8").lower()
    for bad in ("api_key=", "sk-", "ghp_", "password="):
        assert bad not in text
