"""Exécute le benchmark TP04 (mono-A, mono-B, cascade V2) sur des cas JSONL.

Usage (démo, sans API) :
  python -m src.run_benchmark --mode demo --cases experiments/tp04_cases.jsonl --out experiments/results/tp04_demo

Mode live (après autorisation explicite des coûts/données et modèle/licence
vérifiés ; le fichier de configuration ne contient jamais de clé API) :
  python -m src.run_benchmark --mode live --config config/tp04_models.json \
      --cases experiments/tp04_cases.jsonl --confirm-paid-calls \
      --out experiments/results/tp04_live

Sans --config, la configuration live est lue depuis les variables LLM_A_* /
LLM_B_* et TP04_* (voir src/model_config.py). Le mode démo ne prouve jamais la
qualité d'un LLM : il valide uniquement l'orchestration.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List

from .model_config import BenchmarkPolicy, load_config, load_config_from_env
from .orchestrator import CaseInput, DemoClient, OpenAICompatibleClient, Orchestrator, result_to_dict
from .scoring import auto_score_case, summarize as summarize_scores


def load_cases(path: str) -> List[CaseInput]:
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cases.append(CaseInput(**obj))
    return cases


def build_clients(mode: str, config_path: str | None = None):
    """Retourne (client A, client B, politique, mode_live).

    En mode live, l'identité des modèles, la licence, les droits, la région, la
    rétention et le budget sont validés avant tout appel par model_config.
    """
    if mode == "demo":
        # Comportements démo pour valider l'orchestration, PAS la qualité LLM.
        a = DemoClient("demo-model-a", provider="demo", version="demo-a", behavior={
            "case_id=T07": "refuse",
            "case_id=T08": "refuse",
            "case_id=T09": "refuse",
            "case_id=T10": "refuse",
        })
        b = DemoClient("demo-model-b", provider="demo", version="demo-b", behavior={
            "case_id=T08": "ok",
        })
        return a, b, BenchmarkPolicy(), False

    spec_a, spec_b, policy = (
        load_config(config_path) if config_path else load_config_from_env()
    )
    a = OpenAICompatibleClient(
        model_name=spec_a.model_name,
        provider=spec_a.provider,
        version=spec_a.version,
        base_url=spec_a.base_url,
        api_key_env=spec_a.api_key_env,
        spec=spec_a,
    )
    b = OpenAICompatibleClient(
        model_name=spec_b.model_name,
        provider=spec_b.provider,
        version=spec_b.version,
        base_url=spec_b.base_url,
        api_key_env=spec_b.api_key_env,
        spec=spec_b,
    )
    return a, b, policy, True


def write_outputs(rows: List[dict], out_prefix: str) -> None:
    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = out.with_suffix(".jsonl")
    csv_path = out.with_suffix(".csv")

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "case_id", "case_category", "strategy", "status", "reason", "model", "version", "call_count",
        "total_latency_ms", "input_tokens", "output_tokens", "cost_eur", "error_types", "auto_score", "score_note", "notes"
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            traces = row.get("traces", [])
            writer.writerow({
                "case_id": row.get("case_id") or (traces[0]["case_id"] if traces else None),
                "case_category": row.get("case_category"),
                "strategy": row["strategy"],
                "status": row["status"],
                "reason": row["reason"],
                "model": row.get("model"),
                "version": row.get("version"),
                "call_count": sum(t.get("call_count", 0) for t in traces),
                "total_latency_ms": sum(t.get("latency_ms", 0) or 0 for t in traces),
                "input_tokens": sum(t.get("input_tokens", 0) or 0 for t in traces) or None,
                "output_tokens": sum(t.get("output_tokens", 0) or 0 for t in traces) or None,
                "cost_eur": None if all(t.get("cost_eur") is None for t in traces) else sum(t.get("cost_eur", 0) or 0 for t in traces),
                "error_types": "|".join([t.get("error_type") for t in traces if t.get("error_type")]),
                "auto_score": row.get("auto_score"),
                "score_note": row.get("note"),
                "notes": " || ".join([t.get("notes", "") for t in traces if t.get("notes")]),
            })

    print(f"Wrote {jsonl_path}")
    print(f"Wrote {csv_path}")


def load_env_file(path: str) -> None:
    """Charge un fichier KEY=VALUE simple (sans écraser les variables déjà définies)."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Env file not found: {p}")
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--cases", default="experiments/tp04_cases.jsonl")
    parser.add_argument("--out", default="experiments/results/tp04_demo")
    parser.add_argument("--confirm-paid-calls", action="store_true")
    parser.add_argument("--config", default=None, help="JSON A/B + politique (sans clé API), voir config/tp04_models.example.json")
    parser.add_argument("--env-file", default=None, help="Fichier KEY=VALUE (ne pas committer de secrets)")
    parser.add_argument("--scoring-grid", default=None, help="Grille de scoring TP04 JSON (métadonnées)")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file)

    if args.mode == "live" and not args.confirm_paid_calls:
        raise SystemExit("Refusing live mode without --confirm-paid-calls. Vérifier droits, région, rétention et budget avant tout appel.")

    cases = load_cases(args.cases)
    model_a, model_b, policy, live = build_clients(args.mode, args.config)
    orch = Orchestrator(model_a=model_a, model_b=model_b, policy=policy, live=live)

    rows = []
    for case in cases:
        for result in [orch.run_mono(case, "A"), orch.run_mono(case, "B"), orch.run_routing(case), orch.run_cascade(case)]:
            row = result_to_dict(result)
            row["case_id"] = case.case_id
            row["case_category"] = case.category
            score = auto_score_case(case.category, result.status, result.reason)
            row.update(score)
            rows.append(row)

    write_outputs(rows, args.out)
    summary = summarize_scores(rows)
    summary["_meta"] = {
        "mode": args.mode,
        "live": live,
        "cases": args.cases,
        "evidence": "orchestration smoke test uniquement, pas une preuve de qualité LLM" if not live
                    else "exécution live à relire par revue humaine avant tout GO/NO-GO",
    }
    if args.scoring_grid:
        summary["_meta"]["scoring_grid"] = args.scoring_grid
    summary_path = Path(args.out).with_name(Path(args.out).name + "_summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
