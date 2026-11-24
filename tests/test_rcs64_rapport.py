"""RCS-64 — les chiffres du rapport correspondent aux CSV de résultats."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "31_rcs64_comparaison_j2.md").read_text(encoding="utf-8")


def rows(name):
    with open(ROOT / "experiments" / "results" / name, encoding="utf-8") as f:
        return {(r["variant"], r["strategy"]): r for r in csv.DictReader(f)}


def test_quality_values_match_summary():
    s = rows("tp04_local_summary.csv")
    for strat in ("mono_a", "mono_b", "routing", "cascade"):
        q = f"{float(s[('default', strat)]['quality']):.2f}".replace(".", ",")
        assert q in DOC, (strat, q)


def test_same_cases_for_every_strategy():
    s = rows("tp04_local_summary.csv")
    assert {r["n"] for r in s.values()} == {"10"}


def test_limits_and_status_are_explicit():
    for word in ("estimée", "hypothétique", "ND", "Limites explicites"):
        assert word in DOC


def test_traces_are_metadata_only_and_match_summary():
    import json
    from collections import Counter
    allowed = {"trace_id","case_id","variant","strategy","status","models","call_count","latency_ms","input_tokens","output_tokens","cost_eur","score"}
    for stem in ("tp04_local", "tp05_lever"):
        records = [json.loads(line) for line in (ROOT / "experiments" / "results" / (stem + "_traces.jsonl")).read_text(encoding="utf-8").splitlines()]
        assert all(set(r) <= allowed for r in records)
        counts = Counter((r["variant"],r["strategy"]) for r in records)
        summary = rows(stem + "_summary.csv")
        assert counts == {key:int(r["n"]) for key,r in summary.items()}
        assert len({r["trace_id"] for r in records}) == len(records)
