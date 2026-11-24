"""CLI du baseline mono-LLM reproductible (RCS-61).

Usage :
  python -m src.run_baseline_mono \
      --cases experiments/rcs61_workload.jsonl \
      --out experiments/results/rcs61_baseline_mono

La commande exécute deux fois le workload avec le même client déterministe et
échoue si les digests diffèrent. Les fichiers produits sont des logs logiciels,
pas une mesure de qualité LLM.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .baseline_mono import (
    DEFAULT_WORKLOAD,
    load_workload,
    run_baseline,
    verify_reproducibility,
    write_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline mono-LLM reproductible (RCS-61)")
    parser.add_argument("--cases", default=str(DEFAULT_WORKLOAD))
    parser.add_argument("--out", default="experiments/results/rcs61_baseline_mono")
    parser.add_argument("--model-label", choices=["A", "B"], default="A")
    args = parser.parse_args()

    cases = load_workload(args.cases)
    reproducible = verify_reproducibility(cases, model_label=args.model_label)
    if not reproducible:
        raise SystemExit("Exécutions non reproductibles : digests différents")

    bundle = run_baseline(cases, model_label=args.model_label)
    write_outputs(bundle, args.out, reproducible=reproducible)
    summary_path = Path(args.out).with_name(Path(args.out).name + "_summary.json")
    print(f"Wrote {Path(args.out).with_suffix('.jsonl')}")
    print(f"Wrote {Path(args.out).with_suffix('.csv')}")
    print(f"Wrote {summary_path}")
    print(json.dumps({"reproducibility_digest": bundle["reproducibility_digest"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
