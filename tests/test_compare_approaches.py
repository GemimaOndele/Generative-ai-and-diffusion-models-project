"""Tests du module de comparaison RCS-22."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

from src.compare_approaches import (
    APPROACHES,
    BENCHMARK_AXES,
    HYPOTHESES,
    PROTOCOL,
    TICKET_METADATA,
    acceptance_check,
    benchmark_matrix,
    document_alignment_check,
    provisional_choice,
    render_comparison_table,
    render_hypotheses_table,
    validate_no_results,
    validate_ticket_metadata,
)


class CompareApproachesTest(unittest.TestCase):
    @staticmethod
    def _root() -> Path:
        return Path(__file__).resolve().parents[1]

    def test_three_approaches_plus_v2(self):
        self.assertEqual([approach.id for approach in APPROACHES], ["A", "B", "C", "V2"])
        self.assertEqual(len(HYPOTHESES), 4)

    def test_hypotheses_are_falsifiable(self):
        for hypothesis in HYPOTHESES:
            self.assertTrue(hypothesis.statement)
            self.assertTrue(hypothesis.falsifier)
            self.assertTrue(hypothesis.metric)
            self.assertEqual(hypothesis.status, "ND")

    def test_protocol_stays_nd(self):
        self.assertTrue(PROTOCOL)
        self.assertTrue(all(axis.status == "ND" for axis in PROTOCOL))
        self.assertEqual(validate_no_results(), [])

    def test_provisional_choice_is_not_a_go(self):
        choice = provisional_choice()
        self.assertEqual(choice["reference"], "B. règles / ML")
        self.assertIn("provisoire", choice["status"])
        self.assertTrue(choice["reversal"])

    def test_rendered_table_contains_all_jira_axes(self):
        table = render_comparison_table()
        for approach in APPROACHES:
            self.assertIn(approach.id, table)
            self.assertIn(approach.name, table)
        for column in ("Qualité", "Diversité", "Coût initial", "Coût exploitation",
                       "Limites", "Faisabilité", "Preuve"):
            self.assertIn(column, table)
        hypotheses = render_hypotheses_table()
        self.assertIn("Réfutation", hypotheses)
        self.assertIn("| ND |", hypotheses)

    def test_benchmark_matrix_covers_five_axes(self):
        matrix = benchmark_matrix()
        self.assertEqual(tuple(matrix["axes"]), BENCHMARK_AXES)
        self.assertEqual({row["id"] for row in matrix["approaches"]}, {"A", "B", "C", "V2"})
        for row in matrix["approaches"]:
            self.assertEqual(tuple(row["axes"]), BENCHMARK_AXES)

    def test_validation_rejects_invented_measure(self):
        bad = replace(APPROACHES[1], quality="F1 = 0.91")
        approaches = (APPROACHES[0], bad, APPROACHES[2], APPROACHES[3])
        errors = validate_no_results(approaches=approaches)
        self.assertTrue(any("mesure chiffrée" in error for error in errors))

    def test_validation_rejects_missing_falsifier_and_final_go(self):
        bad = replace(HYPOTHESES[0], falsifier="")
        errors = validate_no_results(hypotheses=(bad,) + HYPOTHESES[1:])
        self.assertTrue(any("H1.falsifier" in error for error in errors))

        choice = provisional_choice()
        choice["status"] = "GO final"
        self.assertTrue(any("GO final" in error for error in validate_no_results(choice=choice)))

    def test_acceptance_checks_all_jira_criteria(self):
        result = acceptance_check()
        self.assertTrue(result["ok"], result["criteria"])
        self.assertEqual(len(result["criteria"]), 9)
        self.assertTrue(all(item["ok"] for item in result["criteria"]))
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            {item["id"] for item in result["criteria"]},
            {
                "THREE_APPROACHES_BENCHMARKED", "FIVE_JIRA_AXES", "FALSIFIABLE_HYPOTHESES",
                "JUSTIFIED_CHOICE", "NO_INVENTED_RESULTS", "TRACEABLE_SOURCES",
                "JIRA_TICKET_FIELDS", "DOC_JIRA_ALIGNMENT", "SCIENTIFIC_ANALYSIS",
            },
        )

    def test_jira_ticket_metadata_is_complete_and_not_invented(self):
        self.assertEqual(validate_ticket_metadata(), [])
        self.assertEqual(TICKET_METADATA["source"], "Backlog RoboCare Sentinel V3")
        self.assertIn("S1", TICKET_METADATA["phase"])
        self.assertEqual(TICKET_METADATA["domain"], "BIZ")
        self.assertEqual(TICKET_METADATA["category"], "Fonctionnel")
        self.assertEqual(TICKET_METADATA["competence"], "Analyse scientifique")
        self.assertEqual(
            TICKET_METADATA["roles"],
            {"owner": "Elias", "binome": "Aminata", "relais": "Omar", "reviewer": "Gémima"},
        )
        self.assertEqual(len(TICKET_METADATA["volets"]), 3)

        broken = dict(TICKET_METADATA, competence="")
        self.assertTrue(any("ticket.competence" in error for error in validate_ticket_metadata(broken)))

    def test_document_alignment_detects_missing_jira_field(self):
        source = (self._root() / "docs" / "03_comparaison_statuquo_reglesml_diffusion.md")
        original = source.read_text(encoding="utf-8")
        self.assertTrue(document_alignment_check(source)["ok"])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "doc.md"
            target.write_text(
                original.replace("Analyse scientifique", "à définir").replace("analyse scientifique", "à définir"),
                encoding="utf-8",
            )
            result = document_alignment_check(target)
            self.assertFalse(result["ok"])
            self.assertIn("analyse scientifique", result["missing"])
            self.assertFalse(acceptance_check(target)["ok"])

    def test_committed_acceptance_evidence_matches_code(self):
        evidence = self._root() / "governance" / "rcs22_acceptance.json"
        self.assertTrue(evidence.exists())
        self.assertEqual(json.loads(evidence.read_text(encoding="utf-8")), acceptance_check())

    def test_cli_json_and_acceptance_output(self):
        from src.compare_approaches import main

        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])

        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--acceptance"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "evidence.json"
            with redirect_stdout(io.StringIO()):
                code = main(["--acceptance", "--out", str(target)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), acceptance_check())


if __name__ == "__main__":
    unittest.main()
