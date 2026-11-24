"""Rejeu reproductible du notebook RCS-55 sans serveur Jupyter.

Le notebook ne contient que des cellules Python standards : elles peuvent être
exécutées dans l'ordre, dans un espace de noms neuf, avec la racine du dépôt
comme répertoire courant. Cela permet de vérifier en CI que le notebook est
réellement rejouable et que ses mesures concordent avec l'artefact conservé.

Usage :
  python experiments/replay_baseline_notebook.py
  python experiments/replay_baseline_notebook.py --out "$RUNNER_TEMP/rcs55_notebook_replay.json"
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "experiments" / "baseline_rules_ml.ipynb"
ARTIFACT = ROOT / "experiments" / "results" / "rcs55_baseline_rules_ml.json"


def _charger_notebook(chemin: Path) -> Dict[str, Any]:
    nb = json.loads(chemin.read_text(encoding="utf-8"))
    if nb.get("nbformat") != 4:
        raise ValueError(f"nbformat inattendu pour {chemin} : {nb.get('nbformat')}")
    return nb


def replay_notebook(chemin: Path | None = None, racine: Path | None = None) -> Dict[str, Any]:
    """Exécute les cellules de code du notebook et retourne sorties + espace de noms."""
    racine = Path(racine or ROOT).resolve()
    chemin = Path(chemin or NOTEBOOK).resolve()
    nb = _charger_notebook(chemin)
    cellules = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    if not cellules:
        raise ValueError(f"Aucune cellule de code dans {chemin}")

    espace: Dict[str, Any] = {"__name__": "__rcs55_notebook_replay__", "__file__": str(chemin)}
    sorties: List[Dict[str, Any]] = []
    precedent = Path.cwd()
    os.chdir(racine)
    try:
        for index, cellule in enumerate(cellules, start=1):
            source = "".join(cellule.get("source", []))
            tampon = io.StringIO()
            try:
                with redirect_stdout(tampon):
                    exec(compile(source, f"{chemin.name}:cellule{index}", "exec"), espace)
            except Exception as exc:
                raise RuntimeError(
                    f"Échec du rejeu du notebook, cellule de code {index} "
                    f"(id={cellule.get('id')!r}) : {exc}"
                ) from exc
            sorties.append(
                {
                    "index": index,
                    "id": cellule.get("id"),
                    "stdout": tampon.getvalue().strip(),
                }
            )
    finally:
        os.chdir(precedent)

    return {
        "notebook": str(chemin.relative_to(racine)),
        "cells_executed": len(cellules),
        "outputs": sorties,
        "namespace": espace,
    }


def _egal(left: Any, right: Any) -> bool:
    """Comparaison tolérante sur les flottants (arithmétique multiplateforme)."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_egal(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_egal(a, b) for a, b in zip(left, right))
    if isinstance(left, float) or isinstance(right, float):
        try:
            return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-12)
        except (TypeError, ValueError):
            return False
    return left == right


def comparer_artefact(
    rejeu: Dict[str, Any], artefact: Dict[str, Any]
) -> Tuple[List[str], Dict[str, Any]]:
    """Compare les valeurs calculées par le notebook à l'artefact conservé."""
    espace = rejeu["namespace"]
    cfg = espace["cfg"]
    resultats = espace["resultats"]
    observe = {
        "config": vars(cfg),
        "protocol": resultats["protocol"],
        "thresholds": resultats["thresholds"],
        "dataset": resultats["dataset"],
        "rules_calibration": espace["calibration"].as_dict(),
        "rules_baseline": espace["resultats_rules"],
        "isolation_forest_baseline": resultats["isolation_forest_baseline"],
    }
    differences = [cle for cle, valeur in observe.items() if not _egal(valeur, artefact.get(cle))]
    return differences, observe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", default=str(NOTEBOOK))
    parser.add_argument("--artifact", default=str(ARTIFACT))
    parser.add_argument("--out", default=None, help="Preuve JSON du rejeu (optionnelle)")
    args = parser.parse_args()

    rejeu = replay_notebook(Path(args.notebook))
    artefact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    differences, observe = comparer_artefact(rejeu, artefact)

    preuve = {
        "schema": "rcs55_notebook_replay/v1",
        "status": "reproduced" if not differences and artefact.get("status") == "computed" else "MISMATCH",
        "notebook": rejeu["notebook"],
        "artifact": str(Path(args.artifact).resolve().relative_to(ROOT)),
        "cells_executed": rejeu["cells_executed"],
        "differences": differences,
        "checked_keys": sorted(observe),
        "scope": "smoke test synthétique ; aucune mesure clinique ni seuil gelé",
    }
    if args.out:
        sortie = Path(args.out)
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(json.dumps(preuve, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Preuve de rejeu écrite : {sortie}")

    print(json.dumps(preuve, ensure_ascii=False, indent=2))
    if differences:
        print(f"Écarts notebook/artefact : {', '.join(differences)}")
        return 1
    if artefact.get("status") != "computed":
        print("Artefact en statut ND : aucune mesure à comparer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
