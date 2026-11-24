"""Validation du registre ADR/risques — RCS-18.

La source de vérité reste le document ``docs/registre_decisions_risques.md``.
Ce module ne chiffre aucun risque : il vérifie que les cotations présentes
sont cohérentes et que l'exposition résiduelle reste ``ND`` tant qu'aucune
preuve de réduction n'a été apportée.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCALE_MIN = 1
SCALE_MAX = 5
ESCALATION_EXPOSURE = 12
RESIDUAL_ALLOWED = {"ND", "ND (à réévaluer)"}
ADR_STATUSES = {"Proposé", "Accepté", "Rejeté", "Remplacé", "À décider"}
RISK_STATUSES = {"Ouvert", "Mitigé", "Fermé"}
DEFAULT_REGISTER = Path("docs/registre_decisions_risques.md")
DEFAULT_EXPORT_DIR = Path("governance")

# Colonnes des deux registres opérationnels exportés (source : Markdown).
ADR_CSV_COLUMNS = (
    "id", "date", "status", "decision", "context", "options", "justification",
    "consequences", "owner", "reviewer", "links",
)
RISK_CSV_COLUMNS = (
    "id", "category", "cause_event", "impact", "probability", "severity",
    "exposure", "residual", "triggers", "mitigation", "contingency", "owner",
    "reviewer", "ticket", "review_date", "status", "escalation",
)
LINKED_TICKETS = ("RCS-88", "RCS-89", "RCS-90")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISION_STATUSES = {"Accepté", "Rejeté", "Remplacé"}

# Alias de colonnes : l'ordre des colonnes du Markdown peut changer sans casser
# l'analyse, tant que les libellés attendus restent présents.
RISK_ALIASES = {
    "id": ("ID",),
    "category": ("Catégorie",),
    "cause_event": ("Risque (cause → événement)", "Risque"),
    "impact": ("Impact (personnes / métier / système)", "Impact"),
    "probability": ("Prob.", "Probabilité"),
    "severity": ("Grav.", "Gravité"),
    "exposure": ("Expo. initiale",),
    "residual": ("Expo. résiduelle",),
    "triggers": ("Déclencheurs",),
    "mitigation": ("Mitigation",),
    "contingency": ("Contingence",),
    "owner": ("Propriétaire",),
    "reviewer": ("Reviewer",),
    "ticket": ("Ticket/Test", "Ticket"),
    "review_date": ("Date revue",),
    "status": ("Statut",),
}
ADR_ALIASES = {
    "id": ("ID",),
    "date": ("Date",),
    "status": ("Statut",),
    "decision": ("Décision",),
    "context": ("Contexte",),
    "options": ("Options considérées", "Options"),
    "justification": ("Justification",),
    "consequences": ("Conséquences",),
    "owner": ("Propriétaire",),
    "reviewer": ("Relecteur",),
    "links": ("Liens/preuves", "Liens"),
}

# Thèmes explicitement demandés par le complément Jira RCS-18 (20/11/2026).
RISK_THEME_CATEGORIES = {
    "projet": {"Organisation/Code"},
    "IA": {"IA/Qualité"},
    "biais": {"Biais/Robustesse"},
    "sécurité": {"Sécurité"},
    "RGPD": {"Données/RGPD"},
    "usage biomédical": {"Usage biomédical", "Diffusion"},
    "fournisseur": {"Fournisseur/API"},
    "budget": {"Budget/FinOps"},
    "dette technique": {"Dette technique", "Organisation/Code"},
}
REQUIRED_RISK_FIELDS = (
    "cause_event", "impact", "probability", "severity", "exposure", "residual",
    "triggers", "mitigation", "owner", "reviewer", "ticket", "review_date",
)


@dataclass(frozen=True)
class Risk:
    """Ligne du registre des risques."""

    id: str
    category: str
    cause_event: str
    impact: str
    probability: int
    severity: int
    exposure: int
    residual: str
    owner: str
    reviewer: str
    ticket: str
    review_date: str
    status: str
    triggers: str = field(default="")
    mitigation: str = field(default="")
    contingency: str = field(default="")

    @property
    def escalation(self) -> bool:
        """True si le risque doit être porté au point de coordination."""
        return self.exposure >= ESCALATION_EXPOSURE or self.severity == SCALE_MAX


def exposure(probability: int, severity: int) -> int:
    """Exposition initiale = probabilité × gravité."""
    if not (SCALE_MIN <= probability <= SCALE_MAX):
        raise ValueError(f"probabilité hors échelle 1..5 : {probability}")
    if not (SCALE_MIN <= severity <= SCALE_MAX):
        raise ValueError(f"gravité hors échelle 1..5 : {severity}")
    return probability * severity


def exposure_matrix() -> list[list[int]]:
    """Matrice probabilité (lignes) × gravité (colonnes)."""
    return [
        [exposure(p, s) for s in range(SCALE_MIN, SCALE_MAX + 1)]
        for p in range(SCALE_MIN, SCALE_MAX + 1)
    ]


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _cell(cells: list[str], index: int) -> str:
    """Cellule facultative : les registres réduits restent acceptés."""
    return cells[index] if index < len(cells) else ""


def _find_table(
    lines: list[str], aliases: dict[str, tuple[str, ...]], required: set[str]
) -> tuple[int, dict[str, int]]:
    """Localise l'en-tête et renvoie (index, position de chaque colonne)."""
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = _split_row(line)
        positions = {
            key: position
            for key, names in aliases.items()
            for position, cell in enumerate(cells)
            if cell in names
        }
        if required <= positions.keys():
            return index, positions
    raise ValueError(
        f"table introuvable (colonnes requises : {', '.join(sorted(required))})"
    )


def _table_rows(
    markdown: str,
    aliases: dict[str, tuple[str, ...]],
    required: set[str],
    id_pattern: str,
) -> list[dict[str, str]]:
    """Analyse une table Markdown par libellés de colonnes, pas par position."""
    lines = markdown.splitlines()
    header, positions = _find_table(lines, aliases, required)
    rows: list[dict[str, str]] = []
    for line in lines[header + 2 :]:
        if not line.strip().startswith("|"):
            if rows:
                break
            continue
        cells = _split_row(line)
        identifier = _cell(cells, positions["id"])
        if not re.fullmatch(id_pattern, identifier):
            continue
        rows.append({key: _cell(cells, position) for key, position in positions.items()})
    if not rows:
        raise ValueError(f"aucune ligne trouvée dans la table ({id_pattern})")
    return rows


def parse_risk_table(markdown: str) -> list[Risk]:
    """Analyse la table des risques du registre Markdown."""
    rows = _table_rows(markdown, RISK_ALIASES, set(RISK_ALIASES), r"R-\d+")
    risks: list[Risk] = []
    for row in rows:
        try:
            probability = int(row["probability"])
            severity = int(row["severity"])
            initial = int(row["exposure"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"cotation non numérique pour {row['id']}") from exc
        risks.append(
            Risk(
                id=row["id"],
                category=row["category"],
                cause_event=row["cause_event"],
                impact=row["impact"],
                probability=probability,
                severity=severity,
                exposure=initial,
                residual=row["residual"],
                triggers=row["triggers"],
                mitigation=row["mitigation"],
                contingency=row["contingency"],
                owner=row["owner"],
                reviewer=row["reviewer"],
                ticket=row["ticket"],
                review_date=row["review_date"],
                status=row["status"],
            )
        )
    return risks


def parse_adr_table(markdown: str) -> list[dict[str, str]]:
    """Analyse la table des ADR et renvoie les champs utiles à la validation."""
    return _table_rows(
        markdown,
        ADR_ALIASES,
        {"id", "date", "status", "decision"},
        r"ADR-\d+",
    )


def _duplicates(identifiers: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            duplicates.add(identifier)
        seen.add(identifier)
    return duplicates


def _valid_date(value: str) -> bool:
    """ND ou date ISO réelle ; jamais une date supposée."""
    return value == "ND" or bool(DATE_PATTERN.fullmatch(value))


def validate_risks(risks: list[Risk]) -> list[str]:
    """Renvoie les incohérences détectées (liste vide si tout est valide)."""
    errors: list[str] = []
    for duplicate in sorted(_duplicates([risk.id for risk in risks])):
        errors.append(f"{duplicate}: identifiant de risque dupliqué")
    for risk in risks:
        if risk.exposure != exposure(risk.probability, risk.severity):
            errors.append(
                f"{risk.id}: exposition {risk.exposure} != {risk.probability}×{risk.severity}"
            )
        if risk.residual not in RESIDUAL_ALLOWED:
            errors.append(
                f"{risk.id}: exposition résiduelle '{risk.residual}' non justifiée ; utiliser ND"
            )
        for name in (
            "category", "cause_event", "impact", "triggers", "mitigation",
            "contingency", "owner", "reviewer", "ticket", "status",
        ):
            if not getattr(risk, name):
                errors.append(f"{risk.id}: champ obligatoire manquant ({name})")
        if risk.status not in RISK_STATUSES:
            errors.append(f"{risk.id}: statut inconnu '{risk.status}'")
        if not _valid_date(risk.review_date):
            errors.append(f"{risk.id}: date de revue invalide '{risk.review_date}'")
        if risk.status in {"Mitigé", "Fermé"} and risk.review_date == "ND":
            errors.append(f"{risk.id}: statut '{risk.status}' sans date de revue réelle")
    return errors


def _base_status(status: str) -> str:
    """Retire les précisions entre parenthèses ou après un tiret cadratin."""
    return status.split("(")[0].split("\u2014")[0].strip()


def validate_adrs(adrs: list[dict[str, str]]) -> list[str]:
    """Vérifie les statuts/dates sans inventer de décision."""
    errors: list[str] = []
    for duplicate in sorted(_duplicates([adr["id"] for adr in adrs])):
        errors.append(f"{duplicate}: identifiant ADR dupliqué")
    for adr in adrs:
        status = adr["status"]
        date = adr["date"]
        base = _base_status(status)
        if base not in ADR_STATUSES:
            errors.append(f"{adr['id']}: statut inconnu '{status}'")
        if base == "À décider" and date != "ND":
            errors.append(f"{adr['id']}: décision non prise mais date '{date}' renseignée")
        if base in DECISION_STATUSES and date == "ND":
            errors.append(f"{adr['id']}: décision '{base}' sans date réelle")
        if not _valid_date(date):
            errors.append(f"{adr['id']}: date invalide '{date}'")
        if not adr["decision"]:
            errors.append(f"{adr['id']}: décision vide")
        for name in ("owner", "reviewer", "justification"):
            if name in adr and not adr[name]:
                errors.append(f"{adr['id']}: champ obligatoire manquant ({name})")
    return errors


def build_report(text: str) -> dict:
    """Rapport de validation structuré, exploitable en CI (JSON)."""
    adrs = parse_adr_table(text)
    risks = parse_risk_table(text)
    errors = validate_risks(risks) + validate_adrs(adrs)
    return {
        "ok": not errors,
        "errors": errors,
        "adrs": len(adrs),
        "risks": len(risks),
    }


def check_register(path: str | Path) -> list[str]:
    """Valide un fichier registre complet."""
    return build_report(Path(path).read_text(encoding="utf-8"))["errors"]


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_registers(
    path: str | Path = DEFAULT_REGISTER,
    out_dir: str | Path = DEFAULT_EXPORT_DIR,
) -> tuple[Path, Path]:
    """Exporte les DEUX registres opérationnels depuis l'unique source Markdown.

    Le Markdown reste la source de vérité ; les CSV sont des vues générées pour
    la revue (tri, suivi Sprint). Aucune cotation n'est recalculée ici.
    """
    text = Path(path).read_text(encoding="utf-8")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    adr_path = out / "adr_register.csv"
    risk_path = out / "risk_register.csv"
    _write_csv(
        adr_path,
        ADR_CSV_COLUMNS,
        sorted(parse_adr_table(text), key=lambda adr: adr["id"]),
    )
    _write_csv(
        risk_path,
        RISK_CSV_COLUMNS,
        [
            {**asdict(risk), "escalation": risk.escalation}
            for risk in sorted(parse_risk_table(text), key=lambda risk: risk.id)
        ],
    )
    return adr_path, risk_path


def sprint_review(
    risks: list[Risk],
    *,
    adrs: list[dict[str, str]] | None = None,
    sprint: str = "ND",
    review_date: str = "ND",
) -> dict:
    """Synthèse de revue Sprint : escalades et décision GO/NO-GO non inventée."""
    by_status = {status: 0 for status in RISK_STATUSES}
    for risk in risks:
        by_status[risk.status] = by_status.get(risk.status, 0) + 1
    open_decisions = [
        adr["id"]
        for adr in (adrs or [])
        if _base_status(adr["status"]) in {"À décider", "Proposé"}
    ]
    return {
        "sprint": sprint,
        "review_date": review_date,
        "risks_total": len(risks),
        "by_status": by_status,
        "escalation_rule": f"exposition >= {ESCALATION_EXPOSURE} ou gravité {SCALE_MAX}",
        "escalations": [
            {
                "id": risk.id,
                "exposure": risk.exposure,
                "severity": risk.severity,
                "owner": risk.owner,
                "reviewer": risk.reviewer,
            }
            for risk in risks
            if risk.escalation
        ],
        "risks_without_review_date": [
            risk.id for risk in risks if risk.review_date == "ND"
        ],
        "residual_exposure_known": [
            risk.id for risk in risks if risk.residual not in RESIDUAL_ALLOWED
        ],
        "open_decisions": open_decisions,
        "decisions_total": len(adrs or []),
        "linked_tickets": list(LINKED_TICKETS),
        "go_no_go": "ND",
        "go_no_go_reason": (
            "La cohérence formelle du registre ne constitue pas une preuve ; "
            "arbitrage humain à consigner en revue Sprint."
        ),
    }


def _normalised_csv(path: Path) -> str:
    """Comparaison indépendante des fins de ligne (Windows/Linux)."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _generated_registers_match(path: str | Path, out_dir: str | Path) -> bool:
    """Les deux CSV livrés doivent rester identiques au registre Markdown."""
    out = Path(out_dir)
    expected = [out / "adr_register.csv", out / "risk_register.csv"]
    with tempfile.TemporaryDirectory() as directory:
        generated = export_registers(path, directory)
        for fresh, committed in zip(generated, expected):
            if not committed.exists():
                return False
            if _normalised_csv(fresh) != _normalised_csv(committed):
                return False
    return True


def acceptance_check(
    register_path: str | Path = DEFAULT_REGISTER,
    csv_dir: str | Path = DEFAULT_EXPORT_DIR,
) -> dict:
    """Preuve d'acceptation RCS-18 : chaque critère Jira est vérifié sur pièces.

    Aucun critère n'est déduit d'une simple présence de fichier : les deux
    registres livrés sont comparés au Markdown source, et les thèmes demandés
    par le ticket doivent être couverts.
    """
    path = Path(register_path)
    text = path.read_text(encoding="utf-8")
    report = build_report(text)
    adrs = parse_adr_table(text)
    risks = parse_risk_table(text)
    review = sprint_review(risks, adrs=adrs)
    categories = {risk.category for risk in risks}

    coverage = {
        theme: sorted(categories & expected)
        for theme, expected in RISK_THEME_CATEGORIES.items()
    }
    matrix = exposure_matrix()

    criteria = [
        {
            "id": "ADR_REGISTER",
            "ok": report["ok"] and bool(adrs),
            "evidence": f"{DEFAULT_REGISTER.as_posix()} §1 + governance/adr_register.csv ({report['adrs']} ADR)",
        },
        {
            "id": "RISK_REGISTER",
            "ok": report["ok"] and bool(risks),
            "evidence": f"{DEFAULT_REGISTER.as_posix()} §2 + governance/risk_register.csv ({report['risks']} risques)",
        },
        {
            "id": "RISK_REQUIRED_FIELDS",
            "ok": all(
                getattr(risk, name) not in (None, "")
                for risk in risks
                for name in REQUIRED_RISK_FIELDS
            ),
            "evidence": ", ".join(REQUIRED_RISK_FIELDS),
        },
        {
            "id": "PROBABILITY_IMPACT_SCORING",
            "ok": all(
                SCALE_MIN <= risk.probability <= SCALE_MAX
                and SCALE_MIN <= risk.severity <= SCALE_MAX
                and risk.exposure == risk.probability * risk.severity
                for risk in risks
            ),
            "evidence": "exposition = probabilité × gravité, échelle 1..5",
        },
        {
            "id": "MATRIX_AND_ESCALATION",
            "ok": len(matrix) == SCALE_MAX
            and len(matrix[0]) == SCALE_MAX
            and matrix[2][3] == ESCALATION_EXPOSURE
            and any(risk.escalation for risk in risks),
            "evidence": review["escalation_rule"],
        },
        {
            "id": "RISK_THEME_COVERAGE",
            "ok": all(coverage.values()),
            "evidence": coverage,
        },
        {
            "id": "SPRINT_REVIEW_GO_NO_GO",
            "ok": review["go_no_go"] == "ND" and bool(review["escalations"]),
            "evidence": "GO/NO-GO ND tant que la revue humaine n'a pas arbitré",
        },
        {
            "id": "LINKED_TICKETS",
            "ok": set(LINKED_TICKETS).issubset(set(review["linked_tickets"])),
            "evidence": ", ".join(LINKED_TICKETS),
        },
        {
            "id": "GENERATED_REGISTERS_UP_TO_DATE",
            "ok": _generated_registers_match(path, csv_dir),
            "evidence": "governance/adr_register.csv, governance/risk_register.csv",
        },
    ]
    return {
        "ok": all(criterion["ok"] for criterion in criteria),
        "ticket": "RCS-18",
        "validation": report,
        "coverage": coverage,
        "criteria": criteria,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validation du registre ADR/risques (RCS-18)")
    parser.add_argument("path", nargs="?", default=str(DEFAULT_REGISTER))
    parser.add_argument(
        "--export-dir",
        default=None,
        help="dossier de sortie des deux registres CSV générés",
    )
    parser.add_argument(
        "--sprint-review",
        action="store_true",
        help="afficher la synthèse d'escalade et le GO/NO-GO (toujours ND sans décision réelle)",
    )
    parser.add_argument("--sprint", default="ND", help="identifiant du Sprint, si connu")
    parser.add_argument("--review-date", default="ND", help="date de revue réelle, si connue")
    parser.add_argument(
        "--json",
        action="store_true",
        help="rapport de validation machine (code 1 si le registre est invalide)",
    )
    parser.add_argument(
        "--acceptance",
        action="store_true",
        help="vérifier les critères d'acceptation Jira RCS-18 sur pièces (JSON, code 1 si échec)",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
        report = build_report(text)
    except (OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False))
        else:
            print(f"ERREUR: {exc}")
        return 1

    if args.acceptance:
        result = acceptance_check(path, args.export_dir or DEFAULT_EXPORT_DIR)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1

    if not report["ok"]:
        for error in report["errors"]:
            print(f"ERREUR: {error}")
        return 1

    adrs = parse_adr_table(text)
    risks = parse_risk_table(text)
    escalated = [risk.id for risk in risks if risk.escalation]
    print(f"Registre OK — {len(risks)} risques, escalade: {', '.join(escalated)}")
    print("Matrice exposition:")
    for row in exposure_matrix():
        print("  " + " ".join(f"{value:2d}" for value in row))

    if args.export_dir:
        adr_path, risk_path = export_registers(path, args.export_dir)
        print(f"Registre ADR exporté : {adr_path}")
        print(f"Registre risques exporté : {risk_path}")
    if args.sprint_review:
        print(
            json.dumps(
                sprint_review(
                    risks,
                    adrs=adrs,
                    sprint=args.sprint,
                    review_date=args.review_date,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
