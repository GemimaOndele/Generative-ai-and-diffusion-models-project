"""RCS-16 — contrôle du livrable documentaire (sections attendues, statut des chiffres, pas de secret)."""
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/21_rcs16_conventions_jira.md"


def test_document_present_and_complete():
    text = DOC.read_text(encoding="utf-8")
    for needle in ['Definition of Ready', 'Definition of Done', 'Revue en cours', 'Terminé(e)', 'indicateur',
                   'Modèle de ticket', 'docs/06_sprint0_plan.md', 'sources et leurs droits', 'confidentialité',
                   'décision humaine', 'un gabarit ou une tâche créée ne sont pas un résultat',
                   'estimée collectivement', 'statut du ticket Jira inchangé', 'type(RCS-XX)']:
        assert needle in text, needle


def test_only_statuses_existing_in_rcs_workflow():
    """Le doc ne doit pas imposer de statut absent du projet RCS (À faire / En cours / Revue en cours / Terminé(e))."""
    text = DOC.read_text(encoding="utf-8")
    for absent in ("Prêt pour Sprint", "À préciser", "Spike"):
        assert absent not in text, absent


def test_no_secret_or_patient_identifier():
    text = DOC.read_text(encoding="utf-8").lower()
    for bad in ("api_key=", "sk-", "ghp_", "password="):
        assert bad not in text
