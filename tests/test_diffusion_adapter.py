"""Contrôles RCS-57 : essais contrôlés, seeds, logs, deux variantes, reproductibilité.

Ces tests vérifient le logiciel et la traçabilité de l'exécution synthétique.
Ils ne prouvent ni performance de détection, ni validityé médicale.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.diffusion_adapter import (
    DEFAULT_CONFIG,
    DEFAULT_PROOF_PATH,
    DEFAULT_RUN_PATH,
    LIMITS,
    TICKET_METADATA,
    VARIANTS,
    acceptance_check,
    config_fingerprint,
    linear_schedule,
    main,
    run_experiment,
    validate_run,
    validate_ticket_metadata,
)

ROOT = Path(__file__).resolve().parents[1]


class DiffusionAdapterTest(unittest.TestCase):
    def test_ticket_metadata_is_complete(self):
        self.assertEqual(validate_ticket_metadata(), [])
        self.assertEqual(TICKET_METADATA["key"], "RCS-57")
        self.assertEqual(TICKET_METADATA["acceptance"], "Exécution reproductible et outputs conservés")
        self.assertEqual(len(TICKET_METADATA["volets"]), 3)
        for role in ("responsable", "binome", "relais", "relecteur"):
            self.assertTrue(TICKET_METADATA["roles"][role])

    def test_two_variants_are_controlled(self):
        result = run_experiment()
        self.assertEqual(list(result["variants"]), list(VARIANTS))
        self.assertEqual(result["schedule"], "linear, identique pour les deux variantes")
        base = result["variants"]["base"]
        adapte = result["variants"]["adapte"]
        self.assertFalse(base["conditionnement_temporel"])
        self.assertTrue(adapte["conditionnement_temporel"])
        self.assertEqual(base["seed"], adapte["seed"])
        self.assertEqual(result["config"]["lr"], DEFAULT_CONFIG.lr)
        self.assertEqual(result["config"]["epochs"], DEFAULT_CONFIG.epochs)

    def test_schedule_and_signals_are_deterministic(self):
        beta, alpha_bar = linear_schedule(DEFAULT_CONFIG)
        self.assertEqual(len(beta), DEFAULT_CONFIG.timesteps)
        self.assertEqual(len(alpha_bar), DEFAULT_CONFIG.timesteps)
        self.assertTrue(all(0.0 < value < 1.0 for value in alpha_bar))
        self.assertTrue(all(alpha_bar[i] > alpha_bar[i + 1] for i in range(len(alpha_bar) - 1)))
        again = linear_schedule(DEFAULT_CONFIG)
        self.assertEqual((beta, alpha_bar), again)

    def test_same_seed_replays_identical_logs_and_metrics(self):
        first = run_experiment()
        second = run_experiment()
        for name in VARIANTS:
            self.assertEqual(first["variants"][name]["epoch_losses"], second["variants"][name]["epoch_losses"])
            self.assertEqual(
                first["variants"][name]["reconstruction_mse"],
                second["variants"][name]["reconstruction_mse"],
            )

    def test_different_seed_changes_the_run(self):
        from dataclasses import replace

        changed = run_experiment(replace(DEFAULT_CONFIG, seed=DEFAULT_CONFIG.seed + 1))
        original = run_experiment()
        self.assertNotEqual(changed["run_id"], original["run_id"])
        self.assertNotEqual(
            changed["variants"]["base"]["epoch_losses"],
            original["variants"]["base"]["epoch_losses"],
        )

    def test_logs_have_positive_finite_losses(self):
        result = run_experiment()
        for name in VARIANTS:
            losses = result["variants"][name]["epoch_losses"]
            self.assertEqual(len(losses), DEFAULT_CONFIG.epochs)
            self.assertTrue(all(value > 0 for value in losses))
            self.assertEqual(result["variants"][name]["final_train_loss"], losses[-1])
            self.assertGreater(result["variants"][name]["reconstruction_mse"], 0)

    def test_limits_exclude_medical_claims_and_threshold_freeze(self):
        joined = " ".join(LIMITS)
        self.assertIn("synthétiques", joined)
        self.assertIn("ND", joined)
        self.assertIn("pas une optimisation", joined)
        self.assertNotIn("validé cliniquement", joined)

    def test_acceptance_checks_all_criteria(self):
        proof = acceptance_check()
        self.assertTrue(proof["ok"], proof["errors"])
        self.assertEqual(len(proof["criteria"]), 9)
        self.assertTrue(all(item["ok"] for item in proof["criteria"]))
        self.assertEqual(
            {item["id"] for item in proof["criteria"]},
            {
                "TICKET_FIELDS", "TWO_CONTROLLED_VARIANTS", "FIXED_SEEDS",
                "HYPERPARAMETERS_LOGGED", "LOGS_PRESERVED", "OUTPUTS_PRESERVED",
                "REPRODUCIBLE_EXECUTION", "NO_INVENTED_RESULTS", "SCOPE_J1_SYNTHETIC",
            },
        )
        self.assertEqual(proof["config_fingerprint"], config_fingerprint())

    def test_acceptance_fails_on_absent_or_tampered_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "absent.json"
            self.assertFalse(acceptance_check(missing)["ok"])

            bad = Path(folder) / "bad.json"
            tampered = run_experiment()
            tampered["variants"]["base"]["reconstruction_mse"] = 0.000001
            bad.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
            proof = acceptance_check(bad)
            self.assertFalse(proof["ok"])
            self.assertFalse(
                [item for item in proof["criteria"] if item["id"] == "REPRODUCIBLE_EXECUTION"][0]["ok"]
            )

    def test_structural_errors_block_acceptance_even_without_replay(self):
        from copy import deepcopy
        original = run_experiment()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for field, value in (("ticket", "INVALID"), ("data", []), ("variants", []), ("limits", 3)):
                with self.subTest(field=field):
                    bad = deepcopy(original)
                    bad[field] = value
                    path.write_text(json.dumps(bad), encoding="utf-8")
                    proof = acceptance_check(path)
                    self.assertFalse(proof["ok"])
                    self.assertTrue(proof["errors"])
                    criterion = next(c for c in proof["criteria"] if c["id"] == "REPRODUCIBLE_EXECUTION")
                    self.assertFalse(criterion["ok"])
            path.write_text("[]", encoding="utf-8")
            self.assertFalse(acceptance_check(path)["ok"])

    def test_cli_writes_run_and_acceptance_proof(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "run.json"
            proof_out = Path(folder) / "proof.json"
            self.assertEqual(main(["--out", str(out)]), 0)
            self.assertTrue(out.exists())
            self.assertEqual(validate_run(json.loads(out.read_text(encoding="utf-8"))), [])
            self.assertEqual(
                main(["--acceptance", "--out", str(out), "--proof-out", str(proof_out)]), 0
            )
            proof = json.loads(proof_out.read_text(encoding="utf-8"))
            self.assertTrue(proof["ok"])

    def test_committed_artifact_matches_code(self):
        run = json.loads(DEFAULT_RUN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate_run(run), [])
        replay = run_experiment()
        for name in VARIANTS:
            saved = run["variants"][name]["epoch_losses"]
            fresh = replay["variants"][name]["epoch_losses"]
            self.assertEqual(len(saved), len(fresh))
            # Cross-platform floating-point arithmetic may differ by a few ULPs.
            for left, right in zip(saved, fresh):
                self.assertAlmostEqual(left, right, places=12)
            self.assertAlmostEqual(
                run["variants"][name]["reconstruction_mse"],
                replay["variants"][name]["reconstruction_mse"],
                places=6,
            )

    def test_committed_proof_matches_acceptance(self):
        proof = json.loads(DEFAULT_PROOF_PATH.read_text(encoding="utf-8"))
        self.assertEqual(proof, acceptance_check())

    def test_ci_replays_acceptance_proof(self):
        """La preuve doit être rejouée en CI, pas seulement vérifiée en local."""
        workflow = (ROOT / ".github/workflows/tp04-tests.yml").read_text(encoding="utf-8")
        self.assertIn("python -m src.diffusion_adapter --acceptance", workflow)
        self.assertIn("experiments/results/rcs57_diffusion_variants.json", workflow)
        self.assertIn("governance/rcs57_acceptance.json", workflow)


if __name__ == "__main__":
    unittest.main()
