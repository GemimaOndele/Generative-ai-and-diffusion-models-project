"""TP03 — POC V1 : entrée -> préparation -> génération -> sauvegarde -> log.

Deux preuves techniques dans le même dépôt :
  --track llm  : V1 assistant documentaire mono-LLM (RAG) vs B0 extractif (sans LLM) vs G1-B sans RAG.
  --track j1   : diffusion (délègue à src/run_j1_diffusion.py, jalon Gen AI).

    python src/run_poc.py --track llm --mode local     # Qwen2.5-0.5B-Instruct en local (CPU)
    python src/run_poc.py --track llm --mode demo      # simulation hors-ligne
    python src/run_poc.py --track j1 --quick
"""
from __future__ import annotations

import argparse
import logging
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rcs import RESULTS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("rcs.poc")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["llm", "j1"], default="llm")
    ap.add_argument("--mode", choices=["demo", "local", "live"], default="demo")
    ap.add_argument("--cases", default=str(ROOT / "experiments" / "test_cases.jsonl"))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.track == "j1":
        sys.argv = ["run_j1_diffusion.py"] + (["--quick"] if args.quick else [])
        runpy.run_path(str(ROOT / "src" / "run_j1_diffusion.py"), run_name="__main__")
        return

    from rcs.j2.bench import build_clients, load_cases, run_strategies, summarize, write_outputs
    from rcs.j2.orchestrator import Orchestrator

    cases = load_cases(args.cases)
    log.info("cas gelés : %d (%s)", len(cases), args.cases)
    a, b = build_clients(args.mode)
    orch = Orchestrator(a, b)
    # B0 = recherche seule ; G1-A = V1 (modèle B + RAG + prompt contraint) ; G1-B = ablation sans RAG
    traces, _ = run_strategies(orch, cases, ["b0_extractive", "mono_b", "mono_b_norag"])
    summary = summarize(traces)
    out = RESULTS / f"tp03_v1_{args.mode}"
    write_outputs(out, traces, summary, [], {"track": "llm", "mode": args.mode, "v1_model": b.name,
                                             "simulation": args.mode == "demo"})
    for s in summary:
        log.info("%-14s qualité=%.2f p95=%.0f ms appels=%d", s["strategy"], s["quality"], s["p95_ms"], s["calls"])
    log.info("sorties : %s_*", out)


if __name__ == "__main__":
    main()
