"""Tests du validateur de registre RCS-18."""

import unittest
from pathlib import Path

from src.governance import (
    check_register,
    exposure,
    exposure_matrix,
    parse_adr_table,
    parse_risk_table,
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

    def test_validate_adrs(self):
        adrs = parse_adr_table(MINIMAL_ADR_TABLE)
        self.assertEqual(validate_adrs(adrs), [])
        bad = [
            {"id": "ADR-999", "date": "2026-01-01", "status": "À décider", "decision": "x"}
        ]
        self.assertTrue(any("date" in error for error in validate_adrs(bad)))

    def test_real_register_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        register = root / "docs" / "registre_decisions_risques.md"
        self.assertTrue(register.exists())
        self.assertEqual(check_register(register), [])


if __name__ == "__main__":
    unittest.main()
