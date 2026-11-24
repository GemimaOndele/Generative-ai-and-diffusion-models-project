"""CodeCarbon pour les SEULES exécutions de code locales de RoboCare Sentinel.

L'outil n'est PAS une mesure de l'énergie des API de LLM distantes.
Aucun résultat de mesure n'est inclus. Utilisation opt-in, dépendance facultative.
"""
from __future__ import annotations

import csv
import math
from contextlib import contextmanager
from pathlib import Path
import re
from typing import Iterator, Optional


def _storage_path(run_id: str, root: Optional[Path] = None) -> Path:
    """Stocke les traces hors du dépôt Git par défaut."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("run_id doit contenir seulement lettres, chiffres, _ ou -")
    base = Path(root) if root is not None else Path.home() / ".local" / "share" / "robocare_sentinel" / "codecarbon"
    return base / run_id


@contextmanager
def tracked_local_run(run_id: str, output_root: Optional[Path] = None) -> Iterator[Path]:
    """Instrumente un vrai traitement Python LOCAL et conserve emissions.csv hors Git.

    Le contexte doit contenir un calcul réel et autorisé. Les résultats sont des
    estimations CodeCarbon dépendant du matériel, du mode, du PUE et de la région.
    """
    try:
        from codecarbon import EmissionsTracker, OutputMethod
    except ImportError as exc:
        raise RuntimeError("Dépendance optionnelle absente : pip install codecarbon") from exc

    destination = _storage_path(run_id, output_root)
    destination.mkdir(parents=True, exist_ok=True)
    tracker = EmissionsTracker(
        project_name="robocare_sentinel",
        output_dir=str(destination),
        output_methods=[OutputMethod.CSV],
        tracking_mode="process",
        log_level="error",
    )
    tracker.start()
    try:
        yield destination
    finally:
        # Stop, y compris lorsqu'une exception se produit dans le code instrumenté.
        tracker.stop()


def read_local_metrics(run_id: str, output_root: Optional[Path] = None) -> dict:
    """Renvoie les derniers champs NON sensibles pertinents du CSV local.

    energy_kwh et co2e_kg sont *estimés* par CodeCarbon selon l'observabilité
    matérielle. Ils ne représentent PAS une empreinte complète d'un appel API.
    """
    path = _storage_path(run_id, output_root) / "emissions.csv"
    if not path.is_file():
        return {
            "run_id": run_id, "boundary": "local_compute",
            "source": "CodeCarbon", "measurement_status": "ND",
            "energy_kwh": None, "co2e_kg": None, "duration_s": None,
        }
    with path.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("CSV CodeCarbon sans enregistrement")
    row = rows[-1]

    def maybe_float(field: str) -> Optional[float]:
        value = row.get(field)
        if value in ("", None):
            return None
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"Métrique CodeCarbon non valide : {field}")
        return number

    energy = maybe_float("energy_consumed")
    emissions = maybe_float("emissions")
    return {
        "run_id": run_id,
        "boundary": "local_compute",
        "source": "CodeCarbon",
        "measurement_status": "estimation_codecarbon" if energy is not None or emissions is not None else "ND",
        "energy_kwh": energy,
        "co2e_kg": emissions,
        "duration_s": maybe_float("duration"),
        "tracking_mode": row.get("tracking_mode"),
        "tool_version": row.get("codecarbon_version"),
        "pue_note": "Vérifier si CodeCarbon a déjà appliqué le PUE ; ne pas l'appliquer deux fois",
    }
