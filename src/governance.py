"""Validation du registre ADR/risques — RCS-18.

La source de vérité reste le document ``docs/registre_decisions_risques.md``.
Ce module ne chiffre aucun risque : il vérifie que les cotations présentes
sont cohérentes et que l'exposition résiduelle reste ``ND`` tant qu'aucune
preuve de réduction n'a été apportée.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCALE_MIN = 1
SCALE_MAX = 5
ESCALATION_EXPOSURE = 12
RESIDUAL_ALLOWED = {"ND", "ND (à réévaluer)"}
ADR_STATUSES = {"Proposé", "Accepté", "Rejeté", "Remplacé", "À décider"}
RISK_STATUSES = {"Ouvert", "Mitigé", "Fermé"}


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


def _find_table(lines: list[str], *required: str) -> int:
    for index, line in enumerate(lines):
        if line.strip().startswith("|") and all(token in line for token in required):
            return index
    raise ValueError(f"table introuvable (attendu : {', '.join(required)})")


def parse_risk_table(markdown: str) -> list[Risk]:
    """Analyse la table des risques du registre Markdown."""
    lines = markdown.splitlines()
    header = _find_table(lines, "| ID |", "Expo. initiale", "Expo. résiduelle")
    risks: list[Risk] = []
    for line in lines[header + 2 :]:
        if not line.strip().startswith("|"):
            if risks:
                break
            continue
        cells = _split_row(line)
        if len(cells) < 16 or not re.fullmatch(r"R-\d+", cells[0]):
            continue
        try:
            probability = int(cells[4])
            severity = int(cells[5])
            initial = int(cells[6])
        except ValueError as exc:
            raise ValueError(f"cotation non numérique pour {cells[0]}") from exc
        risks.append(
            Risk(
                id=cells[0],
                category=cells[1],
                cause_event=cells[2],
                impact=cells[3],
                probability=probability,
                severity=severity,
                exposure=initial,
                residual=cells[7],
                owner=cells[11],
                reviewer=cells[12],
                ticket=cells[13],
                review_date=cells[14],
                status=cells[15],
            )
        )
    if not risks:
        raise ValueError("aucun risque trouvé dans la table")
    return risks


def parse_adr_table(markdown: str) -> list[dict[str, str]]:
    """Analyse la table des ADR et renvoie les champs utiles à la validation."""
    lines = markdown.splitlines()
    header = _find_table(lines, "| ID | Date | Statut | Décision |")
    adrs: list[dict[str, str]] = []
    for line in lines[header + 2 :]:
        if not line.strip().startswith("|"):
            if adrs:
                break
            continue
        cells = _split_row(line)
        if len(cells) < 5 or not re.fullmatch(r"ADR-\d+", cells[0]):
            continue
        adrs.append(
            {
                "id": cells[0],
                "date": cells[1],
                "status": cells[2],
                "decision": cells[3],
            }
        )
    if not adrs:
        raise ValueError("aucun ADR trouvé dans la table")
    return adrs


def validate_risks(risks: list[Risk]) -> list[str]:
    """Renvoie les incohérences détectées (liste vide si tout est valide)."""
    errors: list[str] = []
    for risk in risks:
        if risk.exposure != exposure(risk.probability, risk.severity):
            errors.append(
                f"{risk.id}: exposition {risk.exposure} != {risk.probability}×{risk.severity}"
            )
        if risk.residual not in RESIDUAL_ALLOWED:
            errors.append(
                f"{risk.id}: exposition résiduelle '{risk.residual}' non justifiée ; utiliser ND"
            )
        for field in ("owner", "reviewer", "ticket", "status"):
            if not getattr(risk, field):
                errors.append(f"{risk.id}: champ obligatoire manquant ({field})")
        if risk.status not in RISK_STATUSES:
            errors.append(f"{risk.id}: statut inconnu '{risk.status}'")
    return errors


def _base_status(status: str) -> str:
    """Retire les précisions entre parenthèses ou après un tiret cadratin."""
    return status.split("(")[0].split("\u2014")[0].strip()


def validate_adrs(adrs: list[dict[str, str]]) -> list[str]:
    """Vérifie les statuts/dates sans inventer de décision."""
    errors: list[str] = []
    for adr in adrs:
        status = adr["status"]
        date = adr["date"]
        base = _base_status(status)
        if base not in ADR_STATUSES:
            errors.append(f"{adr['id']}: statut inconnu '{status}'")
        if base == "À décider" and date != "ND":
            errors.append(f"{adr['id']}: décision non prise mais date '{date}' renseignée")
        if base == "Accepté" and date == "ND":
            errors.append(f"{adr['id']}: décision acceptée sans date réelle")
        if not adr["decision"]:
            errors.append(f"{adr['id']}: décision vide")
    return errors


def check_register(path: str | Path) -> list[str]:
    """Valide un fichier registre complet."""
    text = Path(path).read_text(encoding="utf-8")
    return validate_risks(parse_risk_table(text)) + validate_adrs(parse_adr_table(text))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]) if args else Path("docs/registre_decisions_risques.md")
    errors = check_register(path)
    if errors:
        for error in errors:
            print(f"ERREUR: {error}")
        return 1
    risks = parse_risk_table(path.read_text(encoding="utf-8"))
    escalated = [risk.id for risk in risks if risk.escalation]
    print(f"Registre OK — {len(risks)} risques, escalade: {', '.join(escalated)}")
    print("Matrice exposition:")
    for row in exposure_matrix():
        print("  " + " ".join(f"{value:2d}" for value in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
