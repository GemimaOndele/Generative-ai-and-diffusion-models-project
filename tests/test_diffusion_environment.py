"""Vérifications de la preuve d'environnement RCS-56 (unittest, sans pytest)."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "experiments" / "check_diffusion_environment.py"
EVIDENCE_PATH = ROOT / "governance" / "rcs56_gpu_capacity.json"
REQUIRED_KEYS = {
    "python_version", "platform", "system", "machine", "torch_available",
    "packages", "cuda_available", "gpu_count", "gpu_name",
    "torch_probe_status", "measured_at", "interpretation",
}


def load_module():
    spec = importlib.util.spec_from_file_location("check_diffusion_environment", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DiffusionEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env_module = load_module()

    def report_for(self, cuda_available, status="ok"):
        environment = self.env_module.collect_environment()
        probe = {
            "status": status,
            "cuda_available": cuda_available,
            "gpu_count": 1 if cuda_available is True else "ND",
            "gpu_name": "GPU déclaré par torch" if cuda_available is True else "ND",
        }
        return self.env_module.build_report(environment, probe, "2026-11-24T00:00:00+00:00")

    def test_report_structure(self):
        report = self.report_for("ND", status="not_installed")
        self.assertTrue(REQUIRED_KEYS <= set(report))
        self.assertIsInstance(report["torch_available"], bool)
        self.assertIsInstance(report["packages"], dict)
        for name in ("numpy", "sklearn", "pandas"):
            self.assertIn(name, report["packages"])
            self.assertIsInstance(report["packages"][name], bool)
        self.assertIsInstance(datetime.fromisoformat(report["measured_at"]), datetime)
        self.assertEqual(
            set(report["interpretation"]),
            {"diffusion_ts_smoke_test_local", "stdlib_j1_smoke_test"},
        )

    def test_decision_follows_cuda_measurement(self):
        for cuda, status in ((True, "ok"), (False, "ok"), ("ND", "not_installed")):
            with self.subTest(cuda=cuda):
                report = self.report_for(cuda, status)
                diffusion = report["interpretation"]["diffusion_ts_smoke_test_local"]
                expected = "GO" if cuda is True else "NO_GO"
                self.assertEqual(diffusion["decision"], expected)
                if cuda is not True:
                    self.assertEqual(diffusion["reason"], self.env_module.NO_CUDA_REASON)
                self.assertEqual(
                    report["interpretation"]["stdlib_j1_smoke_test"]["decision"], "GO"
                )

    def test_nd_when_information_unavailable(self):
        for status in ("not_installed", "timeout", "error"):
            with self.subTest(status=status):
                report = self.report_for("ND", status)
                self.assertEqual(report["cuda_available"], "ND")
                self.assertEqual(report["gpu_count"], "ND")
                self.assertEqual(report["gpu_name"], "ND")
                self.assertEqual(report["torch_probe_status"], status)
                self.assertEqual(
                    report["interpretation"]["diffusion_ts_smoke_test_local"]["decision"],
                    "NO_GO",
                )

    def test_absent_torch_never_creates_a_gpu(self):
        environment = self.env_module.collect_environment()
        environment["torch_available"] = False
        with mock.patch.object(self.env_module, "collect_environment", return_value=environment):
            with mock.patch.object(self.env_module, "probe_torch", side_effect=AssertionError):
                report = self.env_module.collect()
        self.assertEqual(report["cuda_available"], "ND")
        self.assertEqual(report["gpu_count"], "ND")
        self.assertEqual(report["gpu_name"], "ND")
        self.assertEqual(report["torch_probe_status"], "not_installed")

    def test_no_invented_license_cost_or_driver_value(self):
        report = self.report_for("ND", status="timeout")
        serialized = json.dumps(report, ensure_ascii=False).lower()
        for token in ("licence", "license", "cout", "cost", "prix", "eur", "pilote", "driver"):
            self.assertNotIn(token, serialized)

    def test_saved_evidence_is_valid(self):
        self.assertTrue(EVIDENCE_PATH.is_file(), "preuve d'environnement absente")
        report = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(REQUIRED_KEYS <= set(report))
        self.assertIn(report["cuda_available"], (True, False, "ND"))
        self.assertIsInstance(datetime.fromisoformat(report["measured_at"]), datetime)
        diffusion = report["interpretation"]["diffusion_ts_smoke_test_local"]
        self.assertEqual(
            diffusion["decision"], "GO" if report["cuda_available"] is True else "NO_GO"
        )
        if report["cuda_available"] is not True:
            self.assertEqual(diffusion["reason"], self.env_module.NO_CUDA_REASON)
        self.assertEqual(report["interpretation"]["stdlib_j1_smoke_test"]["decision"], "GO")
        serialized = json.dumps(report, ensure_ascii=False).lower()
        for token in ("licence", "license", "cout", "cost", "prix", "eur", "pilote", "driver"):
            self.assertNotIn(token, serialized)

    def test_cli_writes_requested_path(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "preuve.json"
            with mock.patch.object(self.env_module, "collect", return_value=self.report_for("ND")):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(self.env_module.main(["--out", str(out)]), 0)
            self.assertTrue(out.is_file())
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["cuda_available"], "ND")


if __name__ == "__main__":
    unittest.main()
