"""Collecte reproductible de la capacité GPU locale pour RCS-56.

Script STL uniquement : aucune dépendance n'est requise pour produire la
preuve d'environnement. Les bibliothèques optionnelles sont détectées via
``importlib.util.find_spec`` sans import inutile. Le sondeur CUDA tourne dans
un sous-processus borné dans le temps : un import torch lent ou défaillant
donne ``ND``, jamais une valeur inventée.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ND = "ND"
TORCH_PROBE_TIMEOUT_SECONDS = 15.0
OPTIONAL_PACKAGES = ("numpy", "sklearn", "pandas")
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "governance" / "rcs56_gpu_capacity.json"
NO_CUDA_REASON = "CUDA ND/non disponible localement"

# Écrit dans un fichier temporaire pour ne pas mélanger d'éventuels avertissements
# torch au JSON. Aucune information de licence, coût ou pilote n'est collectée.
_TORCH_PROBE = r'''
import json
import sys

target = sys.argv[1]
result = {"status": "error", "cuda_available": "ND", "gpu_count": "ND", "gpu_name": "ND"}
try:
    import torch
    result["cuda_available"] = bool(torch.cuda.is_available())
    if result["cuda_available"]:
        count = int(torch.cuda.device_count())
        result["gpu_count"] = count
        if count > 0:
            result["gpu_name"] = str(torch.cuda.get_device_name(0))
    result["status"] = "ok"
except Exception as exc:  # torch absent, import défaillant ou API CUDA indisponible
    result["error_type"] = type(exc).__name__
with open(target, "w", encoding="utf-8") as handle:
    json.dump(result, handle)
'''


def module_available(name):
    """Détecte un module sans l'importer (faux si la détection échoue)."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def collect_environment():
    """Faits locaux non liés à torch, tous obtenus la bibliothèque STL."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "torch_available": module_available("torch"),
        "packages": {name: module_available(name) for name in OPTIONAL_PACKAGES},
    }


def _nd_probe(status):
    return {
        "status": status,
        "cuda_available": ND,
        "gpu_count": ND,
        "gpu_name": ND,
    }


def probe_torch(timeout=TORCH_PROBE_TIMEOUT_SECONDS):
    """Interroge torch dans un processus borné ; retombe sur ND proprement."""
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "torch_probe.json"
        try:
            completed = subprocess.run(
                [sys.executable, "-c", _TORCH_PROBE, str(target)],
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return _nd_probe("timeout")
        except OSError:
            return _nd_probe("error")
        if completed.returncode != 0 or not target.is_file():
            return _nd_probe("error")
        try:
            result = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return _nd_probe("error")
        if result.get("status") != "ok" or not isinstance(result.get("cuda_available"), bool):
            return _nd_probe(str(result.get("status", "error")))
        return {
            "status": "ok",
            "cuda_available": result["cuda_available"],
            "gpu_count": result.get("gpu_count", ND),
            "gpu_name": result.get("gpu_name", ND),
        }


def interpret(cuda_available):
    """Décisions explicites, sans extrapolation au-delà de la mesure."""
    if cuda_available is True:
        diffusion = {"decision": "GO", "reason": "CUDA disponible localement"}
    else:
        diffusion = {"decision": "NO_GO", "reason": NO_CUDA_REASON}
    return {
        "diffusion_ts_smoke_test_local": diffusion,
        "stdlib_j1_smoke_test": {
            "decision": "GO",
            "reason": "Aucun GPU requis (référence RCS-57)",
        },
    }


def build_report(environment, probe, measured_at):
    """Assemble le rapport à partir de mesures explicites (aucune inférence)."""
    report = dict(environment)
    report.update(
        {
            "cuda_available": probe.get("cuda_available", ND),
            "gpu_count": probe.get("gpu_count", ND),
            "gpu_name": probe.get("gpu_name", ND),
            "torch_probe_status": probe.get("status", "error"),
            "measured_at": measured_at,
            "interpretation": interpret(probe.get("cuda_available", ND)),
        }
    )
    return report


def collect(timeout=TORCH_PROBE_TIMEOUT_SECONDS):
    """Mesure réelle de l'environnement, y compris la disponibilité CUDA."""
    environment = collect_environment()
    probe = _nd_probe("not_installed")
    if environment["torch_available"]:
        probe = probe_torch(timeout)
    measured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return build_report(environment, probe, measured_at)


def write_report(report, out):
    path = Path(out)
    if not path.is_absolute():
        path = REPO_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help="Fichier JSON de sortie (relatif à la racine du dépôt, défaut : governance/rcs56_gpu_capacity.json)",
    )
    args = parser.parse_args(argv)
    path = write_report(collect(), args.out)
    report = json.loads(path.read_text(encoding="utf-8"))
    decision = report["interpretation"]["diffusion_ts_smoke_test_local"]
    print(f"Preuve écrite : {path}")
    print(f"cuda_available = {report['cuda_available']}")
    print(f"smoke test Diffusion-TS local : {decision['decision']} — {decision['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
