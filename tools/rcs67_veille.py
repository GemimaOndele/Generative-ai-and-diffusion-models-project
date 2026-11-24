"""RCS-67 — veille scientifique datée et journal de décisions traçable.

Les fiches ci-dessous ne reprennent que des références déjà citées dans le
dépôt ou les tickets (CM03, TP04, TP05, documentation CodeCarbon, FinOps
Foundation, Green Software Foundation, CNIL, registre ADR). Aucune lecture
récente, aucune conclusion scientifique et aucune date d'étude ne sont
inventées : `date_lecture` reste ND et la décision reste ND.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ND = "ND"
ISSUE = "RCS-67"
ADR_REL = Path("governance") / "adr_register.csv"
ACCEPTANCE_REL = Path("governance") / "rcs67" / "veille_journal.json"
DOC_REL = Path("docs") / "46_rcs67_veille_journal_decisions.md"

# Dates = dates de citation déjà présentes dans le dépôt / les tickets.
# Ce ne sont pas des dates de lecture du projet, qui restent ND.
FICHES: List[Dict[str, Any]] = [
    {
        "id": "V-01", "titre": "CM03 — première preuve GenAI", "url": ND,
        "date_citation": "2026-11-14",
        "domaine": "cadrage pédagogique",
        "limites": ["support de cours", "aucune validation clinique"],
        "alternatives": ["règles/ML", "diffusion J1"],
        "adr_ids": ["ADR-002"],
    },
    {
        "id": "V-02", "titre": "TP04 — du POC V1 à une V2 Multi-LLM démontrable", "url": ND,
        "date_citation": "2026-11-17",
        "domaine": "orchestration LLM",
        "limites": ["défaut V1 non prouvé", "modèles A/B et seuils ND"],
        "alternatives": ["mono-LLM", "routing A/B", "cascade A→B"],
        "adr_ids": ["ADR-003", "ADR-004"],
    },
    {
        "id": "V-03", "titre": "TP05 — FinOps, Green AI & Éthique", "url": ND,
        "date_citation": "2026-11-20",
        "domaine": "coût, énergie, éthique",
        "limites": ["exercice non exécuté", "statut ND tant que non mesuré"],
        "alternatives": ["API distante", "calcul local", "hybride"],
        "adr_ids": ["ADR-002", "ADR-009"],
    },
    {
        "id": "V-04", "titre": "CodeCarbon — documentation officielle",
        "url": "https://docs.codecarbon.io/latest/",
        "date_citation": "2026-11-20",
        "domaine": "mesure énergie locale",
        "limites": ["ne mesure pas l'énergie d'un serveur distant", "estimation selon le matériel"],
        "alternatives": ["mesure locale", "API non instrumentée", "ND"],
        "adr_ids": ["ADR-002", "ADR-009"],
    },
    {
        "id": "V-05", "titre": "FinOps Foundation — AI FinOps",
        "url": "https://www.finops.org/wg/finops-for-ai-overview/",
        "date_citation": "2026-11-20",
        "domaine": "gouvernance des coûts",
        "limites": ["cadre général", "aucun tarif du projet n'est fourni"],
        "alternatives": ["coût API seul", "coût complet"],
        "adr_ids": ["ADR-009"],
    },
    {
        "id": "V-06", "titre": "Green Software Foundation — SCI-AI",
        "url": "https://greensoftware.foundation/standards/sci-ai/",
        "date_citation": "2026-11-20",
        "domaine": "intensité carbone",
        "limites": ["modèle d'estimation", "périmètre commun à expliciter"],
        "alternatives": ["SCI", "mesure directe", "ND"],
        "adr_ids": ["ADR-002"],
    },
    {
        "id": "V-07", "titre": "CNIL — fiches pratiques IA",
        "url": "https://www.cnil.fr/fr/les-fiches-pratiques-ia",
        "date_citation": "2026-11-20",
        "domaine": "données et conformité",
        "limites": ["un audit technique n'est pas une preuve de conformité", "revue juridique requise"],
        "alternatives": ["minimisation", "anonymisation", "revue juridique"],
        "adr_ids": ["ADR-007"],
    },
    {
        "id": "V-08", "titre": "Registre des décisions et risques (RCS-18)", "url": ND,
        "date_citation": "2026-11-23",
        "domaine": "gouvernance projet",
        "limites": ["la plupart des ADR sont proposés ou à décider", "non ratification collective"],
        "alternatives": ["proposé", "accepté", "rejeté"],
        "adr_ids": ["ADR-001", "ADR-006", "ADR-008"],
    },
]


def load_adr_register(root: Path) -> Dict[str, Dict[str, str]]:
    path = root / ADR_REL
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "id" not in reader.fieldnames:
            raise ValueError("Registre ADR invalide : colonne id absente")
        rows = list(reader)
    register = {row["id"].strip(): row for row in rows if row.get("id", "").strip()}
    if not register:
        raise ValueError("Registre ADR vide")
    return register


def build_report(root: Path) -> Dict[str, Any]:
    register = load_adr_register(root)
    adr_index: Dict[str, Dict[str, Any]] = {
        ident: {"status": row.get("status", ND), "fiches": []}
        for ident, row in register.items()
    }
    fiches: List[Dict[str, Any]] = []
    for raw in FICHES:
        item = dict(raw)
        item["date_lecture"] = ND
        item["statut_lecture"] = ND
        item["decision_scientifique"] = ND
        for ident in item["adr_ids"]:
            if ident in adr_index:
                adr_index[ident]["fiches"].append(item["id"])
        fiches.append(item)

    checks = {
        "fiches_dates_et_sources": all(
            fiche["date_citation"] and fiche["id"] and fiche["url"]
            for fiche in fiches
        ),
        "limites_et_alternatives_presentes": all(
            fiche["limites"] and fiche["alternatives"] for fiche in fiches
        ),
        "adr_ids_existants": all(
            ident in register for fiche in fiches for ident in fiche["adr_ids"]
        ),
        "traceabilite_bidirectionnelle": all(
            fiche["id"] in adr_index[ident]["fiches"]
            for fiche in fiches for ident in fiche["adr_ids"] if ident in register
        ),
        "pas_de_date_lecture_inventee": all(
            fiche["date_lecture"] == ND and fiche["statut_lecture"] == ND
            for fiche in fiches
        ),
    }
    return {
        "schema": "rcs67_veille_journal/v1",
        "issue": ISSUE,
        "fiches": fiches,
        "adr_index": adr_index,
        "checks": checks,
        "traceabilite": "OK" if all(checks.values()) else "INCOMPLETE",
        "decision": ND,
        "note": "Fiches de veille et ADR traçables ; aucune conclusion scientifique n'est produite.",
    }


def serialize(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_doc(report: Dict[str, Any]) -> str:
    lines = [
        f"# {ISSUE} — Veille scientifique et journal de décisions",
        "",
        "> Les fiches ci-dessous reprennent uniquement des références déjà "
        "citées dans le dépôt ou les tickets. `date_lecture = ND` : aucune "
        "lecture récente ni conclusion scientifique n'est inventée.",
        "",
        "## Fiches datées",
        "",
        "| ID | Référence | Date de citation dans le dépôt | Domaine | Limites | Alternatives | ADR |",
        "|---|---|---|---|---|---|---|",
    ]
    for fiche in report["fiches"]:
        lines.append(
            f"| {fiche['id']} | {fiche['titre']} ({fiche['url']}) | "
            f"{fiche['date_citation']} | {fiche['domaine']} | "
            f"{'; '.join(fiche['limites'])} | {'; '.join(fiche['alternatives'])} | "
            f"{', '.join(fiche['adr_ids'])} |"
        )
    lines += [
        "",
        "## Journal ADR ↔ fiches",
        "",
        "| ADR | Statut dans le registre | Fiches liées |",
        "|---|---|---|",
    ]
    for ident, data in report["adr_index"].items():
        if data["fiches"]:
            lines.append(f"| {ident} | {data['status']} | {', '.join(data['fiches'])} |")
    lines += ["", "## Contrôles", "", "| Contrôle | Résultat |", "|---|---|"]
    for name, value in report["checks"].items():
        lines.append(f"| {name} | {'OK' if value else 'ÉCHEC'} |")
    lines += [
        "",
        f"**Traçabilité : {report['traceabilite']} — décision scientifique : {report['decision']}.**",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m tools.rcs67_veille --write",
        "python -m tools.rcs67_veille --check",
        "python -m unittest tests.test_rcs67_veille -v",
        "```",
        "",
        "Sources : `governance/adr_register.csv`, `docs/registre_decisions_risques.md`, "
        "`docs/06_tp05_finops_green_ethique.md`, tickets RCS-62 à RCS-90.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(root: Path, report: Dict[str, Any]) -> None:
    for rel, content in (
        (ACCEPTANCE_REL, serialize(report)),
        (DOC_REL, render_doc(report)),
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs(root: Path, report: Dict[str, Any]) -> tuple[bool, List[str]]:
    reasons: List[str] = []
    for rel, content in (
        (ACCEPTANCE_REL, serialize(report)),
        (DOC_REL, render_doc(report)),
    ):
        path = root / rel
        if not path.is_file():
            reasons.append(f"{rel.as_posix()} absent")
        elif path.read_text(encoding="utf-8") != content:
            reasons.append(f"{rel.as_posix()} obsolète : relancer --write")
    if report["traceabilite"] != "OK":
        reasons.append("traçabilité incomplète entre fiches et ADR")
    if report["decision"] != ND:
        reasons.append("décision scientifique non ND sans preuve d'étude")
    return not reasons, reasons


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-67 — veille et journal de décisions")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.root)
    except (OSError, ValueError) as exc:
        print(str(exc))
        return 1
    if args.write:
        write_outputs(args.root, report)
    if args.check:
        ok, reasons = check_outputs(args.root, report)
        if not ok:
            print("\n".join(reasons))
            return 1
    print(serialize(report), end="")
    return 0 if report["traceabilite"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
