"""RCS-82 — coût par tâche réussie : formules, ND si zéro succès, doublons exclus."""
import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_tp05", ROOT / "src" / "run_tp05.py")
tp05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tp05)


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _summary(variant, strategy, quality, n=10):
    return {"variant": variant, "strategy": strategy, "n": n, "quality": quality, "calls": 10, "input_tokens": 100,
            "output_tokens": 50, "p95_ms": 1000, "errors": 0}


def test_cost_per_success_and_nd_when_zero(tmp_path):
    _write(tmp_path / "tp04_local_summary.csv", [_summary("default", "ok", 0.5), _summary("default", "zero", 0.0)])
    _write(tmp_path / "tp04_local_energy.csv", [
        {"variant": "default", "strategy": "ok", "energy_kwh": 0.002, "co2e_kg": 0.0001},
        {"variant": "default", "strategy": "zero", "energy_kwh": 0.002, "co2e_kg": 0.0001}])
    rows = {r["strategy"]: r for r in tp05.build_rows(tmp_path)}
    assert float(rows["ok"]["cout_par_succes_eur"]) == 0.002 * tp05.ELEC_EUR_PER_KWH / 5
    assert rows["zero"]["cout_par_succes_eur"] == "ND"
    assert rows["ok"]["cout_api_eur"].startswith("0")


def test_measures_distinguished_from_estimates(tmp_path):
    _write(tmp_path / "tp04_local_summary.csv", [_summary("default", "x", 0.4)])
    r = tp05.build_rows(tmp_path)[0]
    assert r["energie_kwh"] == "ND" and r["statut_energie"] == "non mesuré"


def test_committed_table_matches_inputs():
    rows = tp05.build_rows(ROOT / "experiments" / "results")
    keys = [(r["source"], r["variant"], r["strategy"]) for r in rows]
    assert len(keys) == len(set(keys))  # pas de doublon
    with open(ROOT / "experiments" / "results" / "rcs82_tp05_mesures.csv", encoding="utf-8") as f:
        committed = list(csv.DictReader(f))
    assert [r["cout_par_succes_eur"] for r in committed] == [r["cout_par_succes_eur"] for r in rows]


def test_no_personal_data_in_committed_traces():
    """Aucune trace versionnée ne doit contenir d'identité ni de numéro de sécurité sociale (même fictifs)."""
    import json
    import re
    nir = re.compile(r"\b[12]\s?\d{2}\s?(0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}(\s?\d{2})?\b")
    named_patient = re.compile(r"(?i)\bpatient(e)?\s+[A-Z][a-zé]+\s+[A-Z][a-zé]+")
    for path in (ROOT / "experiments" / "results").glob("*.jsonl"):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            text = json.dumps(json.loads(line), ensure_ascii=False)
            assert not nir.search(text), f"{path.name}:{n} contient un motif de NIR"
            assert not named_patient.search(text), f"{path.name}:{n} contient un nom de patient"
