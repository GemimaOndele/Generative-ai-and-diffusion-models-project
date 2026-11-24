"""RCS-70 — tests du manifeste de preuve diffusion (sans résultat inventé)."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.rcs70_diffusion_proof import (
    ACCEPTANCE_REL,
    DOC_REL,
    SCRIPT_REL,
    build_report,
    check_outputs,
    serialize,
    structure_checks,
    write_outputs,
)

REAL_SCRIPT = """\
# démonstrateur synthétique
class Denoiser:
    def train(self, x, rng):
        epsilon = rng.normal(size=x.shape)
        return epsilon

def sample(rng):
    # DDPM reverse sampler
    return rng.normal(size=3)

training_method = "learned_epsilon_MLP_Adam_DDPM_reverse_sampler"
seed = 42
"""

NOISE_ONLY_SCRIPT = """\
import numpy as np
x = np.zeros(3)
bruit = np.random.default_rng(1).normal(size=3)
x = x + bruit
"""


def make_root(directory: Path, script: str = REAL_SCRIPT) -> Path:
    path = directory / SCRIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")
    return directory


def artifact_payload() -> dict:
    return {
        "seed": 42, "numpy_version": "2.2.6", "diffusion_timesteps": 24,
        "train_updates": 250, "dataset_sha256": "abc123",
        "training_runtime_seconds": 1.234, "generated_samples_count": 3,
        "sample_finite": True,
        "scope": "synthetic_signal_research_only_not_medical",
        "scientific_status": "illustrative_experiment_not_clinical_validation",
        "training_method": "learned_epsilon_MLP_Adam_DDPM_reverse_sampler",
        "train_loss_start": 1.0, "train_loss_end": 0.2,
        "baseline_MAD": {"f1": 0.57}, "learned_diffusion_denoiser": {"f1": 0.97},
    }


class Rcs70DiffusionProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_root(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_denoising_script_is_detected(self) -> None:
        checks = structure_checks(REAL_SCRIPT)
        self.assertTrue(all(checks.values()))
        self.assertFalse(any(structure_checks(NOISE_ONLY_SCRIPT).values()))

    def test_no_artifact_means_every_evidence_is_nd(self) -> None:
        report = build_report(self.root)
        self.assertEqual(report["proof_status"], "ND")
        self.assertTrue(report["checks"]["code_debruitage_reel"])
        self.assertFalse(report["checks"]["artefact_present"])
        for value in report["preuves"].values():
            self.assertEqual(value, "ND")
        for value in report["metriques_synthetiques"].values():
            self.assertEqual(value, "ND")

    def test_artifact_is_copied_with_real_hash_only(self) -> None:
        path = self.root / "run.json"
        path.write_text(json.dumps(artifact_payload()), encoding="utf-8")
        report = build_report(self.root, str(path))
        self.assertTrue(report["artefact"]["present"])
        self.assertEqual(
            report["artefact"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
        )
        self.assertEqual(report["preuves"]["seed"], 42)
        self.assertEqual(report["preuves"]["numpy_version"], "2.2.6")
        self.assertEqual(report["proof_status"], "DEMO_SYNTHETIQUE")
        for value in report["checks"].values():
            self.assertTrue(value, value)

    def test_incomplete_artifact_stays_incomplete(self) -> None:
        path = self.root / "partial.json"
        path.write_text(json.dumps({"seed": 42}), encoding="utf-8")
        report = build_report(self.root, str(path))
        self.assertEqual(report["proof_status"], "INCOMPLET")
        self.assertEqual(report["preuves"]["numpy_version"], "ND")
        self.assertFalse(report["checks"]["artefact_complet"])

    def test_missing_artifact_or_script_is_an_error_or_block(self) -> None:
        with self.assertRaises(ValueError):
            build_report(self.root, str(self.root / "absent.json"))
        empty = make_root(Path(tempfile.mkdtemp()), script=NOISE_ONLY_SCRIPT)
        report = build_report(empty)
        self.assertEqual(report["proof_status"], "BLOQUE")
        ok, reasons = check_outputs(empty, report)
        self.assertFalse(ok)
        self.assertTrue(any("débruitage" in reason for reason in reasons))

    def test_no_medical_claim_no_clinical_validation(self) -> None:
        report = build_report(self.root)
        self.assertEqual(report["decision"], "A_TESTER")
        self.assertFalse(report["medical_claim"])
        self.assertFalse(report["clinical_validation"])
        self.assertGreaterEqual(len(report["blocking_reasons"]), 4)

    def test_write_check_deterministic_and_tamper(self) -> None:
        report = build_report(self.root)
        write_outputs(self.root, report)
        first = (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8")
        doc = (self.root / DOC_REL).read_text(encoding="utf-8")
        self.assertEqual(first, serialize(report))
        write_outputs(self.root, build_report(self.root))
        self.assertEqual(first, (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc, (self.root / DOC_REL).read_text(encoding="utf-8"))
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)
        (self.root / ACCEPTANCE_REL).write_text("{}\n", encoding="utf-8")
        ok, reasons = check_outputs(self.root, report)
        self.assertFalse(ok)
        self.assertTrue(any("obsolète" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
