"""TP04 — Benchmark V2 Multi-LLM : B0 extractif, mono-A, mono-B, routing A/B, cascade A→B.

    python run_benchmark.py --mode demo                       # orchestration hors-ligne (SIMULATION)
    python run_benchmark.py --mode local --energy             # 2 vrais LLM ouverts sur CPU + CodeCarbon
    python run_benchmark.py --mode local --ablation           # + ablations (garde-fous OFF, routage seuil)
    python run_benchmark.py --mode live --confirm-paid-calls  # API compatibles Chat Completions (LLM_A_*, LLM_B_*)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from rcs import RESULTS  # noqa: E402
from rcs.j2.bench import build_clients, load_cases, run_strategies, summarize, write_outputs  # noqa: E402
from rcs.j2.orchestrator import Orchestrator  # noqa: E402

STRATS = ["b0_extractive", "mono_a", "mono_b", "routing", "cascade"]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "uncommitted"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["demo", "local", "live"], default="demo")
    ap.add_argument("--cases", default="experiments/rcs77_cases_candidate.jsonl")
    ap.add_argument("--out", default=None)
    ap.add_argument("--energy", action="store_true", help="mesure CodeCarbon par stratégie")
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=120)
    ap.add_argument("--confirm-paid-calls", action="store_true")
    ap.add_argument("--strategies", nargs="+", default=STRATS, choices=STRATS)
    ap.add_argument("--label", default="", help="préfixe de variante (ex. tok60_ pour le levier TP05)")
    args = ap.parse_args()
    if args.mode == "live" and not args.confirm_paid_calls:
        sys.exit("Mode live : ajouter --confirm-paid-calls après autorisation des coûts.")

    out = Path(args.out) if args.out else RESULTS / f"tp04_{args.mode}"
    cases = load_cases(args.cases)
    a, b = build_clients(args.mode, args.max_new_tokens)
    orch = Orchestrator(a, b)
    traces, energy = run_strategies(orch, cases, args.strategies, label=args.label,
                                    measure_energy=args.energy, out_dir=out.parent)

    if args.ablation:
        # Ablation 1 : garde-fous déterministes désactivés (une seule variable)
        t2, e2 = run_strategies(Orchestrator(a, b, use_guards=False), cases, ["mono_a", "mono_b", "cascade"],
                                label="noguards_", measure_energy=args.energy, out_dir=out.parent)
        # Ablation 2 : seuil de complexité du routeur abaissé (plus de cas vers B)
        t3, e3 = run_strategies(Orchestrator(a, b, complexity_words=8), cases, ["routing"],
                                label="route8w_", measure_energy=args.energy, out_dir=out.parent)
        traces += t2 + t3
        energy += e2 + e3

    summary = summarize(traces)
    write_outputs(out, traces, summary, energy, {
        "mode": args.mode, "model_a": a.name, "model_b": b.name, "cases": args.cases,
        "n_cases": len(cases), "git_commit": git_sha(), "max_new_tokens": args.max_new_tokens,
        "simulation": args.mode == "demo",
        "warning": "mode demo = transitions logicielles, PAS une mesure de qualité LLM" if args.mode == "demo" else "",
    })
    print("\nvariant/strategy  quality  usual complex stress  p95_ms  calls  esc")
    for s in summary:
        print(f"{s['variant']:9s} {s['strategy']:14s} {s['quality']:.2f}  {s['quality_usual']:.2f}  "
              f"{s['quality_complex']:.2f}  {s['quality_stress']:.2f}  {s['p95_ms']:8.0f}  {s['calls']:3d}  "
              f"{s['escalations']}")


if __name__ == "__main__":
    main()
