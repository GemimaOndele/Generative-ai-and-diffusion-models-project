"""Tests du validateur de registre RCS-18."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.governance import (
    ADR_CSV_COLUMNS,
    RISK_CSV_COLUMNS,
    check_register,
    exposure,
    exposure_matrix,
    export_registers,
    main,
    parse_adr_table,
    parse_risk_table,
    sprint_review,
    validate_adrs,
    validate_risks,
)

MINIMAL_RISK_TABLE = """
| ID | Catégorie | Risque (cause → événement) | Impact (personnes / métier / système) | Prob. | Grav. | Expo. initiale | Expo. résiduelle | Déclencheurs | Mitigation | Contingence | Propriétaire | Reviewer | Ticket/Test | Date revue | Statut |
|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|---|
| R-001 | Test | Cause → événement | Personnes : x ; Métier : y ; Système : z | 2 | 5 | 10 | ND | déclencheur | mitigation | contingence | Équipe | Omar | RCS-18 | ND | Ouvert |
"""

MINIMAL_ADR_TABLE = """
| ID | Date | Statut | Décision | Contexte |
|---|---|---|---|---|
| ADR-001 | ND | À décider | Choisir équipement pilote | Sprint 0 |
| ADR-002 | 2026-11-23 | Accepté (local) | Socle unique | PR #30 |
"""

REORDERED_RISK_TABLE = """
| Statut | ID | Catégorie | Risque (cause → événement) | Impact (personnes / métier / système) | Grav. | Prob. | Expo. initiale | Expo. résiduelle | Déclencheurs | Mitigation | Contingence | Propriétaire | Reviewer | Ticket/Test | Date revue |
|---:|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|
| Ouvert | R-042 | Test | Cause → événement | Personnes : x ; Métier : y ; Système : z | 5 | 2 | 10 | ND | déclencheur | mitigation | contingence | Équipe | Omar | RCS-18 | ND |
"""


class GovernanceRegisterTest(unittest.TestCase):
    def test_exposure_and_matrix(self):
        self.assertEqual(exposure(3, 4), 12)
        matrix = exposure_matrix()
        self.assertEqual(len(matrix), 5)
        self.assertEqual(matrix[2][3], 12)
        with self.assertRaises(ValueError):
            exposure(0, 4)

    def test_parse_and_validate_risk_table(self):
        risks = parse_risk_table(MINIMAL_RISK_TABLE)
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0].id, "R-001")
        self.assertTrue(risks[0].escalation)
        self.assertEqual(validate_risks(risks), [])

    def test_validate_risks_rejects_invented_residual(self):
        risks = parse_risk_table(
            MINIMAL_RISK_TABLE.replace("| 10 | ND |", "| 10 | 4 |")
        )
        errors = validate_risks(risks)
        self.assertTrue(any("résiduelle" in error for error in errors))

    def test_validate_risks_rejects_wrong_exposure(self):
        risks = parse_risk_table(
            MINIMAL_RISK_TABLE.replace("| 2 | 5 | 10 |", "| 2 | 5 | 9 |")
        )
        errors = validate_risks(risks)
        self.assertTrue(any("exposition 9" in error for error in errors))

    def test_validate_risks_requires_mitigation_and_owner(self):
        risks = parse_risk_table(
            MINIMAL_RISK_TABLE.replace(
                "| déclencheur | mitigation | contingence | Équipe |",
                "| déclencheur | | contingence | |",
            )
        )
        errors = validate_risks(risks)
        self.assertTrue(any("mitigation" in error for error in errors))
        self.assertTrue(any("owner" in error for error in errors))

    def test_validate_adrs(self):
        adrs = parse_adr_table(MINIMAL_ADR_TABLE)
        self.assertEqual(validate_adrs(adrs), [])
        bad = [
            {"id": "ADR-999", "date": "2026-01-01", "status": "À décider", "decision": "x"}
        ]
        self.assertTrue(any("date" in error for error in validate_adrs(bad)))

    @staticmethod
    def _register_path() -> Path:
        return Path(__file__).resolve().parents[1] / "docs" / "registre_decisions_risques.md"

    def test_real_register_is_valid(self):
        register = self._register_path()
        self.assertTrue(register.exists())
        self.assertEqual(check_register(register), [])

    def test_export_produces_two_operational_registers(self):
        with tempfile.TemporaryDirectory() as directory:
            adr_path, risk_path = export_registers(self._register_path(), Path(directory))
            with adr_path.open(encoding="utf-8", newline="") as handle:
                adr_rows = list(csv.DictReader(handle))
            with risk_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(tuple(reader.fieldnames or ()), RISK_CSV_COLUMNS)
                risk_rows = list(reader)

        self.assertEqual(adr_path.name, "adr_register.csv")
        self.assertEqual(risk_path.name, "risk_register.csv")
        self.assertEqual(tuple(adr_rows[0].keys()), ADR_CSV_COLUMNS)
        self.assertEqual(len(adr_rows), 10)
        self.assertEqual(len(risk_rows), 8)
        self.assertEqual(adr_rows[0]["id"], "ADR-001")
        self.assertEqual(risk_rows[0]["id"], "R-001")
        self.assertTrue(risk_rows[0]["mitigation"])
        self.assertEqual(risk_rows[0]["owner"], "Équipe")
        self.assertEqual(risk_rows[0]["escalation"], "True")  # gravité 5

    def test_sprint_review_never_invents_go_no_go(self):
        risks = parse_risk_table(self._register_path().read_text(encoding="utf-8"))
        review = sprint_review(risks, sprint="S0", review_date="ND")
        escalated = {item["id"] for item in review["escalations"]}
        self.assertIn("R-002", escalated)  # exposition 15 et gravité 5
        self.assertIn("R-003", escalated)  # exposition 12
        self.assertEqual(review["residual_exposure_known"], [])
        self.assertEqual(review["linked_tickets"], ["RCS-88", "RCS-89", "RCS-90"])
        self.assertEqual(review["go_no_go"], "ND")
        self.assertEqual(review["sprint"], "S0")

    def test_cli_validates_exports_and_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([str(self._register_path()), "--export-dir", directory, "--sprint-review"])
            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertIn("Registre ADR exporté", text)
            self.assertIn("Registre risques exporté", text)
            self.assertIn('"go_no_go": "ND"', text)
            self.assertTrue((Path(directory) / "risk_register.csv").exists())

    def test_parse_uses_column_labels_not_positions(self):
        risks = parse_risk_table(REORDERED_RISK_TABLE)
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0].id, "R-042")
        self.assertEqual(risks[0].probability, 2)
        self.assertEqual(risks[0].severity, 5)
        self.assertEqual(validate_risks(risks), [])

    def test_validate_rejects_duplicates_bad_dates_and_unreviewed_closure(self):
        duplicate = MINIMAL_RISK_TABLE + MINIMAL_RISK_TABLE.strip().splitlines()[-1] + "\n"
        self.assertTrue(
            any("dupliqué" in error for error in validate_risks(parse_risk_table(duplicate)))
        )
        bad_date = MINIMAL_RISK_TABLE.replace(
            "| RCS-18 | ND | Ouvert |", "| RCS-18 | 24/11/2026 | Ouvert |"
        )
        self.assertTrue(
            any(
                "date de revue invalide" in error
                for error in validate_risks(parse_risk_table(bad_date))
            )
        )
        closed = MINIMAL_RISK_TABLE.replace(
            "| RCS-18 | ND | Ouvert |", "| RCS-18 | ND | Fermé |"
        )
        self.assertTrue(
            any(
                "sans date de revue réelle" in error
                for error in validate_risks(parse_risk_table(closed))
            )
        )

    def test_review_lists_open_decisions_and_unreviewed_risks(self):
        text = self._register_path().read_text(encoding="utf-8")
        review = sprint_review(parse_risk_table(text), adrs=parse_adr_table(text), sprint="S0")
        self.assertIn("ADR-006", review["open_decisions"])
        self.assertEqual(review["decisions_total"], 10)
        self.assertIn("R-001", review["risks_without_review_date"])
        self.assertEqual(review["escalation_rule"], "exposition >= 12 ou gravité 5")

    def test_cli_json_report_and_clean_parse_error(self):
        valid = io.StringIO()
        with redirect_stdout(valid):
            code = main([str(self._register_path()), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(valid.getvalue())
        self.assertEqual(payload, {"ok": True, "errors": [], "adrs": 10, "risks": 8})

        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.md"
            invalid.write_text(
                MINIMAL_RISK_TABLE.replace("| 2 | 5 | 10 |", "| 2 | 5 | 9 |")
                + MINIMAL_ADR_TABLE,
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([str(invalid), "--json"])
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(output.getvalue())["ok"])

            broken = Path(directory) / "broken.md"
            broken.write_text("Registre sans table", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([str(broken)])
            self.assertEqual(code, 1)
            self.assertTrue(output.getvalue().startswith("ERREUR:"))


if __name__ == "__main__":
    unittest.main()
