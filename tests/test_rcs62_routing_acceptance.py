"""RCS-62 — tests du protocole d'acceptation du routage Multi-LLM."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.rcs62_routing_acceptance import (
    ACCEPTANCE_REL,
    DOC_REL,
    ROUTE_CASES,
    build_cascade_orchestrators,
    build_orchestrator,
    build_report,
    check_outputs,
    serialize,
    write_outputs,
)
from src.orchestrator import CaseInput


class Rcs62RoutingAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = build_report()

    def test_report_requires_three_distinct_route_cases(self) -> None:
        self.assertEqual(len(self.report["cases"]), 3)
        self.assertEqual(
            [row["category"] for row in self.report["cases"]],
            ["usual", "complex", "sensitive"],
        )
        self.assertEqual(len({row["case_id"] for row in self.report["cases"]}), 3)
        self.assertEqual(ROUTE_CASES[0]["case_id"], "T01")
        self.assertEqual(ROUTE_CASES[2]["category"], "sensitive")

    def test_two_distinct_models_and_default_guards(self) -> None:
        self.assertTrue(self.report["checks"]["deux_modeles_distincts"])
        self.assertTrue(self.report["checks"]["garde_fous_actifs"])
        orch = build_orchestrator()
        self.assertNotEqual(orch.spec_a.identity(), orch.spec_b.identity())
        self.assertEqual(orch.policy.max_calls_per_case, 2)
        self.assertFalse(orch.policy.allow_paid_calls)

    def test_route_uses_category_not_expected_behavior(self) -> None:
        by_id = {row["case_id"]: row for row in self.report["cases"]}
        self.assertEqual(by_id["T01"]["route_observee"], "A")
        self.assertEqual(by_id["T05"]["route_observee"], "B")
        self.assertEqual(by_id["T10"]["route_observee"], "A")
        for row in self.report["cases"]:
            self.assertEqual(row["route_observee"], row["route_avec_expected_modifie"])
        self.assertTrue(self.report["checks"]["selection_par_categorie_uniquement"])

    def test_report_reconciles_expected_route_selected_route_and_effective_status(self) -> None:
        """Régression relecture ff7aad7 : T05 devait annoncer B, pas A."""
        by_id = {row["case_id"]: row for row in self.report["cases"]}
        self.assertEqual(by_id["T01"]["route_attendue"], "A")
        self.assertEqual(by_id["T05"]["route_interne_attendue"], "B")
        self.assertEqual(by_id["T05"]["route_attendue"], "B")
        self.assertEqual(by_id["T10"]["route_interne_attendue"], "A")
        self.assertEqual(by_id["T10"]["route_attendue"], "refus")
        for row in self.report["cases"]:
            self.assertEqual(row["route_observee"], row["route_interne_attendue"])
            self.assertEqual(row["decision_effective_observee"], row["decision_effective_attendue"])
            if row["category"] == "sensitive":
                self.assertEqual(row["decision_effective_observee"], "refused")
                self.assertTrue(row["transfert_bloque_avant_appel"])
                self.assertEqual(row["routing"]["call_count"], 0)
            else:
                self.assertEqual(row["route_attendue"], row["route_observee"])
                self.assertEqual(row["decision_effective_observee"], "ok")
        self.assertTrue(self.report["checks"]["route_effective_conforme_au_rapport"])
        self.assertTrue(self.report["checks"]["selection_par_categorie_uniquement"])

    def test_cascade_fallback_actually_runs_allowed_and_blocked(self) -> None:
        """Le rapport ne se contente pas de déclarer le repli : il l'exécute."""
        allowed, blocked = build_cascade_orchestrators()
        probe = dict(ROUTE_CASES[1])
        probe["input"] = "force-fallback " + probe["input"]
        case = CaseInput(**probe)

        ok = allowed.run_cascade(case)
        self.assertEqual(ok.status, "ok")
        self.assertEqual(ok.reason, "validated_by_b")
        self.assertEqual(sum(trace.call_count for trace in ok.traces), 2)
        self.assertEqual([trace.decision for trace in ok.traces], ["try_a", "fallback_to_b"])

        refused = blocked.run_cascade(case)
        self.assertEqual(refused.status, "abstain")
        self.assertEqual(refused.reason, "fallback_blocked")
        self.assertEqual(sum(trace.call_count for trace in refused.traces), 1)
        self.assertEqual([trace.decision for trace in refused.traces], ["try_a"])
        self.assertNotIn("fallback_to_b", [trace.decision for trace in refused.traces])

        sensitive = build_orchestrator().run_cascade(CaseInput(**ROUTE_CASES[2]))
        self.assertEqual(sensitive.status, "refused")
        self.assertEqual(sensitive.reason, "transfer_blocked")
        self.assertEqual(sum(trace.call_count for trace in sensitive.traces), 0)

        probes = self.report["cascade_probes"]
        self.assertEqual(probes["repli_autorise"]["status"], ok.status)
        self.assertEqual(probes["repli_autorise"]["reason"], ok.reason)
        self.assertEqual(probes["repli_autorise"]["call_count"], 2)
        self.assertEqual(probes["repli_refuse"]["status"], refused.status)
        self.assertEqual(probes["repli_refuse"]["reason"], refused.reason)
        self.assertEqual(probes["repli_refuse"]["call_count"], 1)
        self.assertEqual(probes["cas_sensible"]["status"], sensitive.status)
        self.assertEqual(probes["cas_sensible"]["call_count"], 0)
        self.assertTrue(self.report["checks"]["fallback_autorise_effectif"])
        self.assertTrue(self.report["checks"]["fallback_refuse_sans_appel_b"])

    def test_generated_doc_matches_report_route_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_outputs(root, self.report)
            doc = (root / DOC_REL).read_text(encoding="utf-8")
            rows = {
                line.split("|")[1].strip(): line
                for line in doc.splitlines()
                if line.startswith("| T") and "|" in line
            }
            self.assertIn("| B | B | B |", rows["T05"])
            self.assertIn("| A | refus | refused |", rows["T10"])
            json_text = (root / ACCEPTANCE_REL).read_text(encoding="utf-8")
            self.assertIn('"route_attendue": "B"', json_text)
            self.assertIn('"route_attendue": "refus"', json_text)
            ok, reasons = check_outputs(root, self.report)
            self.assertTrue(ok, reasons)

    def test_sensitive_case_refused_before_any_call(self) -> None:
        sensible = [row for row in self.report["cases"] if row["category"] == "sensitive"]
        self.assertEqual(len(sensible), 1)
        self.assertEqual(sensible[0]["routing"]["status"], "refused")
        self.assertEqual(sensible[0]["routing"]["call_count"], 0)
        self.assertTrue(self.report["checks"]["cas_sensible_refuse_sans_appel"])

    def test_transfer_block_is_observed_from_trace_not_declared_from_category(self) -> None:
        """Régression relecture #42 : le blocage sensible doit être constaté."""
        by_id = {row["case_id"]: row for row in self.report["cases"]}
        self.assertEqual(by_id["T10"]["routing"]["reason"], "transfer_blocked")
        self.assertTrue(by_id["T10"]["transfert_bloque_avant_appel"])
        for row in self.report["cases"]:
            self.assertEqual(
                row["transfert_bloque_avant_appel"],
                row["routing"]["reason"] == "transfer_blocked",
                row["case_id"],
            )
        self.assertTrue(self.report["checks"]["transfert_bloque_constate_dans_la_trace"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_outputs(root, self.report)
            doc = (root / DOC_REL).read_text(encoding="utf-8")
            rows = {
                line.split("|")[1].strip(): line
                for line in doc.splitlines()
                if line.startswith("| T") and "|" in line
            }
            self.assertIn("| non |", rows["T01"])
            self.assertIn("| non |", rows["T05"])
            self.assertIn("| oui |", rows["T10"])
            self.assertIn("transfert_bloque_constate_dans_la_trace | OK", doc)

    def test_mono_comparison_present_for_each_case(self) -> None:
        for row in self.report["cases"]:
            self.assertIn(row["mono_a"]["status"], {"ok", "abstain", "refused"})
            self.assertIn(row["mono_b"]["status"], {"ok", "abstain", "refused"})
            self.assertEqual(row["mono_a"]["strategy"], "mono_a")
            self.assertEqual(row["mono_b"]["strategy"], "mono_b")
            self.assertEqual(row["routing"]["strategy"], "routing_a_b")
        self.assertTrue(self.report["checks"]["comparaison_mono_presente"])

    def test_report_has_no_prompt_secret_or_expected_behavior(self) -> None:
        data = json.dumps(self.report, ensure_ascii=False)
        self.assertNotIn("expected_behavior", data)
        self.assertNotIn("cas fictif de maintenance", data)
        self.assertNotIn("sk-", data)
        self.assertTrue(self.report["checks"]["traces_sans_secret_ni_expected"])

    def test_live_decision_stays_no_go(self) -> None:
        self.assertEqual(self.report["demo_gate"], "PASS")
        self.assertEqual(self.report["live_decision"], "NO_GO")
        self.assertFalse(self.report["qualite_llm_mesuree"])
        self.assertGreaterEqual(len(self.report["blocking_reasons"]), 3)

    def test_write_and_check_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_outputs(root, self.report)
            first = (root / "governance/rcs62/acceptance.json").read_text(encoding="utf-8")
            second = (root / "docs/44_rcs62_routing_multillm.md").read_text(encoding="utf-8")
            write_outputs(root, build_report())
            self.assertEqual(first, (root / "governance/rcs62/acceptance.json").read_text(encoding="utf-8"))
            self.assertEqual(second, (root / "docs/44_rcs62_routing_multillm.md").read_text(encoding="utf-8"))
            ok, reasons = check_outputs(root, self.report)
            self.assertTrue(ok, reasons)
            self.assertEqual(first, serialize(self.report))

    def test_check_detects_tampered_or_missing_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok, reasons = check_outputs(root, self.report)
            self.assertFalse(ok)
            self.assertTrue(any("absent" in reason for reason in reasons))
            write_outputs(root, self.report)
            path = root / "governance/rcs62/acceptance.json"
            path.write_text(path.read_text(encoding="utf-8").replace("NO_GO", "GO"), encoding="utf-8")
            ok, reasons = check_outputs(root, self.report)
            self.assertFalse(ok)
            self.assertTrue(any("obsolète" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
