"""RCS-67 — tests de la veille datée et du journal ADR traçable."""
from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.rcs67_veille import (
    ADR_REL,
    FICHES,
    ND,
    ACCEPTANCE_REL,
    DOC_REL,
    build_report,
    check_outputs,
    serialize,
    write_outputs,
)

ADR_IDS = [f"ADR-{i:03d}" for i in range(1, 10)]


def make_root(directory: Path, ids=ADR_IDS) -> Path:
    path = directory / ADR_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["id,date,status,decision"]
    lines += [f"{ident},2026-11-23,Proposé,décision de test" for ident in ids]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return directory


class Rcs67VeilleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_root(Path(self.tmp.name))
        self.report = build_report(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_fiches_have_dates_limits_and_alternatives(self) -> None:
        self.assertEqual(len(self.report["fiches"]), 8)
        self.assertEqual(len({f["id"] for f in self.report["fiches"]}), 8)
        for fiche in self.report["fiches"]:
            self.assertTrue(fiche["date_citation"])
            self.assertTrue(fiche["url"] is not None)
            self.assertGreaterEqual(len(fiche["limites"]), 2)
            self.assertGreaterEqual(len(fiche["alternatives"]), 2)

    def test_dates_are_already_present_in_repository(self) -> None:
        dates = {fiche["date_citation"] for fiche in self.report["fiches"]}
        self.assertEqual(
            dates,
            {"2026-11-14", "2026-11-17", "2026-11-20", "2026-11-23"},
        )
        self.assertEqual({f["date_lecture"] for f in self.report["fiches"]}, {ND})

    def test_no_conclusion_no_reading_date_no_decision(self) -> None:
        for fiche in self.report["fiches"]:
            self.assertEqual(fiche["statut_lecture"], ND)
            self.assertEqual(fiche["decision_scientifique"], ND)
        self.assertEqual(self.report["decision"], ND)
        self.assertTrue(self.report["note"].startswith("Fiches de veille"))

    def test_adr_traceability_is_bidirectional(self) -> None:
        self.assertEqual(self.report["traceabilite"], "OK")
        for name, value in self.report["checks"].items():
            self.assertTrue(value, name)
        for fiche in FICHES:
            for ident in fiche["adr_ids"]:
                self.assertIn(fiche["id"], self.report["adr_index"][ident]["fiches"])

    def test_unknown_adr_breaks_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            root = make_root(Path(other), ids=["ADR-001"])
            report = build_report(root)
            self.assertFalse(report["checks"]["adr_ids_existants"])
            self.assertNotEqual(report["traceabilite"], "OK")
            ok, reasons = check_outputs(root, report)
            self.assertFalse(ok)
            self.assertTrue(any("traçabilité" in reason for reason in reasons))

    def test_duplicate_adr_is_rejected(self) -> None:
        make_root(self.root, ids=ADR_IDS + ["ADR-001"])
        with self.assertRaisesRegex(ValueError, "dupliqué"):
            build_report(self.root)

    def test_missing_adr_id_is_rejected(self) -> None:
        make_root(self.root, ids=ADR_IDS + [""])
        with self.assertRaisesRegex(ValueError, "sans identifiant"):
            build_report(self.root)

    def test_duplicate_fiche_is_rejected(self) -> None:
        with patch("tools.rcs67_veille.FICHES", FICHES + [dict(FICHES[0])]):
            with self.assertRaisesRegex(ValueError, "dupliqué"):
                build_report(self.root)

    def test_invalid_citation_date_is_rejected(self) -> None:
        with patch("tools.rcs67_veille.FICHES", [dict(FICHES[0], date_citation="2026-02-30")]):
            with self.assertRaisesRegex(ValueError, "Date de citation ISO"):
                build_report(self.root)

    def test_missing_register_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises((OSError, ValueError)):
                build_report(Path(other))

    def test_write_check_deterministic_and_tamper(self) -> None:
        write_outputs(self.root, self.report)
        first = (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8")
        doc = (self.root / DOC_REL).read_text(encoding="utf-8")
        self.assertEqual(first, serialize(self.report))
        write_outputs(self.root, build_report(self.root))
        self.assertEqual(first, (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc, (self.root / DOC_REL).read_text(encoding="utf-8"))
        ok, reasons = check_outputs(self.root, self.report)
        self.assertTrue(ok, reasons)
        (self.root / DOC_REL).write_text("modifié", encoding="utf-8")
        ok, reasons = check_outputs(self.root, self.report)
        self.assertFalse(ok)
        self.assertTrue(any("obsolète" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
