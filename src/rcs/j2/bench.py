"""Exécution d'un benchmark : mêmes cas × stratégies, traces brutes + agrégats + énergie (optionnelle)."""
from __future__ import annotations

import csv
import json
import os
import platform
from pathlib import Path

import numpy as np

from .orchestrator import Orchestrator
from .scoring import score

MODEL_A_DEFAULT = "HuggingFaceTB/SmolLM2-360M-Instruct"   # A : petit, économique
MODEL_B_DEFAULT = "Qwen/Qwen2.5-0.5B-Instruct"            # B : plus robuste


def load_cases(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def build_clients(mode: str, max_new_tokens: int = 120):
    from . import llm
    if mode == "demo":
        return llm.DemoClient("demo-A (simulation)"), llm.DemoClient("demo-B (simulation)")
    if mode == "local":
        return (llm.LocalHFClient(os.environ.get("LLM_A_REPO", MODEL_A_DEFAULT), max_new_tokens),
                llm.LocalHFClient(os.environ.get("LLM_B_REPO", MODEL_B_DEFAULT), max_new_tokens))
    if mode == "live":
        return llm.OpenAICompatibleClient("LLM_A"), llm.OpenAICompatibleClient("LLM_B")
    raise ValueError(mode)


def run_strategies(orch: Orchestrator, cases: list[dict], strategies: list[str], label: str = "",
                   measure_energy: bool = False, out_dir: Path | None = None) -> tuple[list[dict], list[dict]]:
    traces, energy = [], []
    for strat in strategies:
        tracker = None
        if measure_energy:
            from codecarbon import OfflineEmissionsTracker
            tracker = OfflineEmissionsTracker(country_iso_code="FRA", project_name=f"{label}{strat}",
                                              output_dir=str(out_dir or "."), save_to_file=False,
                                              log_level="error", measure_power_secs=1)
            tracker.start()
        rows = []
        for case in cases:
            tr = orch.run(case, strat).to_dict()
            tr["score"], tr["score_reason"] = score(case, tr["answer"])
            tr["variant"] = label.rstrip("_") or "default"
            rows.append(tr)
            print(f"{label}{strat:14s} {case['id']} score={tr['score']} route={tr['route']} "
                  f"calls={tr['call_count']} {tr['latency_ms']:.0f}ms {tr['validation']}")
        if tracker:
            kg = tracker.stop()
            data = tracker.final_emissions_data
            energy.append({"variant": label.rstrip("_") or "default", "strategy": strat,
                           "energy_kwh": data.energy_consumed, "co2e_kg": kg,
                           "duration_s": data.duration, "cpu_model": data.cpu_model,
                           "tracking_mode": data.tracking_mode, "country": data.country_iso_code,
                           "status": "estimé (CodeCarbon, modèle CPU/RAM local)"})
        traces += rows
    return traces, energy


def summarize(traces: list[dict]) -> list[dict]:
    out = []
    keys = sorted({(t["variant"], t["strategy"]) for t in traces})
    for variant, strat in keys:
        rows = [t for t in traces if t["variant"] == variant and t["strategy"] == strat]
        lat = np.array([t["latency_ms"] for t in rows])
        cats = {}
        for t in rows:
            cats.setdefault(t["category"], []).append(t["score"])
        out.append({
            "variant": variant, "strategy": strat, "n": len(rows),
            "quality": round(float(np.mean([t["score"] for t in rows])), 3),
            "quality_usual": round(float(np.mean(cats.get("usuel", [np.nan]))), 3),
            "quality_complex": round(float(np.mean(cats.get("complexe", [np.nan]))), 3),
            "quality_stress": round(float(np.mean([t["score"] for t in rows if t["category"] not in
                                                   ("usuel", "complexe")])), 3),
            "p50_ms": round(float(np.percentile(lat, 50)), 1), "p95_ms": round(float(np.percentile(lat, 95)), 1),
            "calls": int(sum(t["call_count"] for t in rows)),
            "input_tokens": int(sum(t["input_tokens"] for t in rows)),
            "output_tokens": int(sum(t["output_tokens"] for t in rows)),
            "errors": int(sum(t["status"] != "ok" for t in rows)),
            "escalations": int(sum(1 for t in rows if str(t["route"]).startswith("A->B"))),
            "routed_to_B": int(sum(1 for t in rows if t["route"] == "B")),
        })
    return out


def write_outputs(prefix: Path, traces: list[dict], summary: list[dict], energy: list[dict], meta: dict) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{prefix}_traces.jsonl", "w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    for name, rows in (("summary", summary), ("energy", energy)):
        if rows:
            with open(f"{prefix}_{name}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    meta = dict(meta, python=platform.python_version(), machine=platform.processor() or platform.machine())
    Path(f"{prefix}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
