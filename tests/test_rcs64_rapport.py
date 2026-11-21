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
