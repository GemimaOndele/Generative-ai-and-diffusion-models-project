"""Tests de cohérence documentaire pour RCS-39 (règles d'automatisation et HITL)."""
from pathlib import Path
import re

DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "40_rcs39_regles_automatisation.md"


def _read_doc() -> str:
    assert DOC_PATH.exists(), f"Document manquant : {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


def test_required_sections_present():
    text = _read_doc()
    for heading in [
        "## 1. Périmètre et contrats de référence",
        "## 2. Matrice Déclencheurs / Actions / Exceptions",
        "## 3. Cycle de vie des statuts et piste d'audit",
    ]:
        assert heading in text, f"Section manquante : {heading}"


def test_rule_ids_complete_and_unique():
    text = _read_doc()
    expected_ids = [f"AUTO-0{i}" for i in range(1, 9)]
    for rule_id in expected_ids:
        assert f"**{rule_id}**" in text, f"Règle manquante dans la matrice : {rule_id}"
    found = re.findall(r"\*\*AUTO-\d{2}\*\*", text)
    assert len(found) == len(set(found)), "Des identifiants AUTO-XX sont dupliqués"


def test_ingestion_and_alerts_contracts_referenced():
    text = _read_doc()
    required_symbols = [
        "sha256_file",
        "validate_row",
        "import_csv",
        "write_manifest",
        "enregistrer_analyse",
        "gravite",
        "decider_alerte",
        "ouvrir_intervention",
        "ROLES_HABILITES",
        "PermissionRefusee",
        "TransitionInvalide",
    ]
    for symbol in required_symbols:
        assert symbol in text, f"Symbole de contrat non référencé : {symbol}"


def test_schema_tables_and_status_enums_aligned():
    text = _read_doc()
    for token in [
        "lot_import",
        "observation",
        "analyse_modele",
        "alerte",
        "intervention",
        "audit",
        "a_qualifier",
        "validee",
        "rejetee",
        "ouverte",
        "en_cours",
        "cloturee",
        "technicien",
        "responsable",
    ]:
        assert token in text, f"Table ou enum SQL manquant : {token}"


def test_hitl_and_bounded_guardrails_documented():
    text = _read_doc().lower()
    assert "aucune action autonome sur un appareil médical réel" in text
    assert "retries" in text and "timeout" in text
    assert "alerte_validee" in text and "alerte_rejetee" in text
    assert "decision_refusee_permission" in text
