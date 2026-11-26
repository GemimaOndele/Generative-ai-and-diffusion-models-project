---
name: robocare-global
description: Règles globales obligatoires du monorepo RoboCare Sentinel (sécurité biomédicale, arborescence, Git/Jira, rigueur scientifique).
---

# Skill Global — RoboCare Sentinel (Monorepo)

## 1. Périmètre et sécurité métier
- RoboCare Sentinel est un logiciel d'aide à la maintenance biomédicale : **ne jamais générer de code qui pilote, configure ou répare automatiquement une machine médicale réelle**.
- Toute décision opérationnelle (validation/rejet d'alerte, ouverture d'intervention) requiert une **validation humaine (HITL)** tracée dans `audit`.
- Aucune donnée patient (PHI/PII), aucun rapport hospitalier brut non autorisé, aucune clé API (`.env`) et aucun dataset volumineux ne doivent être commités dans Git. Utiliser uniquement `data/manifests/`, `data/contracts/` et des échantillons autorisés.
- **Catalogue multi-familles** : ne pas figer une famille d'équipement unique tant que `RCS-19` / `DEC-02` n'est pas tranché ; distinguer explicitement `fictional_demo_only` et `industrial_proxy_non_medical`.

## 2. Architecture du monorepo
- Respecter strictement la séparation des dossiers existants :
  - `docs/` (cadrage, architecture, gouvernance, audits — numérotés `XX_rcsYY_*.md`)
  - `data/` (`contracts/`, `manifests/`, échantillons licites uniquement)
  - `sql/` (`001_init_schema.sql` et migrations versionnées)
  - `src/rcs/` (`db.py`, `ingestion.py`, `alerts.py`, `j1/`) et `src/observability/` (`codecarbon_local.py`)
  - `frontend/monitoring/` (tableaux de bord 4 vues)
  - `experiments/`, `tests/`, `governance/`, `planning/`, `tools/`
- **GitHub Pages** : la vitrine statique vit uniquement sur la branche `gh-pages` (ne pas dupliquer `index.html` / `landing.js` dans `main/docs`).

## 3. Règles Git & Jira obligatoires (`RCS-48`)
- **Jamais de push direct sur `main`**.
- **Une branche temporaire par ticket Jira** depuis `origin/main` à jour : `<type>/RCS-XXX-sujet` (`docs/`, `feature/`, `data/`, `experiment/`, `fix/`, `test/`, `chore/`).
- Tout commit (`<type>(RCS-XXX): description`) et toute Pull Request doivent citer la clé Jira (`RCS-XXX`) et inclure une preuve vérifiable (commande de test, log ou capture).
- Fusion par **Squash and merge** après **au moins 1 approbation humaine indépendante** et CI verte.
- Ne pas modifier les fichiers d'un autre module sans le signaler explicitement.

## 4. Rigueur scientifique et observabilité
- Toujours qualifier explicitement chaque chiffre ou résultat : **mesuré**, **calculé**, **estimé**, **hypothétique** ou **ND** (non disponible).
- Ne jamais présenter un dataset industriel de substitution (ex. AI4I, MIMII DUE) comme de la télémétrie hospitalière réelle.
- **Frontière CodeCarbon** : `src/observability/codecarbon_local.py` mesure uniquement le calcul Python **local** (`local_compute`) ; les appels API LLM distants ont `energy_kwh_status = "ND"`.
