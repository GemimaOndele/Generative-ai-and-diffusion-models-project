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

- **Jamais de push direct sur `main`**. `main` reste la référence stable ; `gh-pages` reste dédiée à la vitrine.
- **Transition** : les PR historiques restent sur leurs branches temporaires jusqu'à leur validation et fusion. Aucun déplacement, duplication, suppression ni réécriture de travaux non intégrés. Tant que les protections et paramètres ci-dessous ne sont pas vérifiés et que cette règle n'est pas approuvée, conserver la méthode historique (branche temporaire par ticket, squash).
- Cible : cinq branches permanentes, chacune pilotée par un responsable :
  - `dev/governance-integration` — Gémima : gouvernance, coordination, architecture et intégration ;
  - `dev/functional-ux-quality` — Aminata : fonctionnel, UX, qualité et éthique ;
  - `dev/data-benchmark` — Omar : données, SQL, JMerise, benchmarks ;
  - `dev/genai-diffusion-llm` — Elias : diffusion, IA générative et Multi-LLM ;
  - `dev/platform-monitoring` — Ayoub : plateforme, monitoring, API et déploiement.
- Les affectations Jira priment sur les périmètres indicatifs ; les binômes coordonnent interfaces et fichiers, sans écraser le travail d'autrui. Un seul pilote par branche, une PR cohérente active par branche autant que possible, avec plusieurs tickets si leurs changements sont liés.
- Avant activation, vérifier l'autorisation des merge commits, la protection des cinq branches contre suppression et force push, et la désactivation de la suppression automatique globale si nécessaire. Conserver les protections de main, résolution des discussions, CI et revue indépendante.
- Synchroniser régulièrement chaque branche avec `origin/main` par merge non forcé, avant développement et avant intégration. Récupérer les dépendances depuis main après revue ; cherry-pick ciblé exceptionnel et coordonné, avec traçabilité. Ne pas copier des dossiers entiers ni importer des PR non validées.
- Tout commit (`<type>(RCS-XXX): description`) et toute Pull Request doivent citer la ou les clés Jira et inclure une preuve vérifiable (commande de test, log ou capture). Ne pas modifier les fichiers d'un autre module sans le signaler.
- Fusion des branches permanentes par **merge commit** (historique commun préservé), après **au moins 1 approbation humaine indépendante** sur les changements actuels, CI verte et résolution des discussions. Ne pas supprimer la branche permanente après fusion ; la resynchroniser sur main.
- Les branches temporaires restent possibles pour une correction isolée ou un risque de conflit ; nom `<type>/RCS-XXX-sujet`, squash après revue et CI, suppression seulement après intégration vérifiée. Aucun push forcé ni auto-approbation.
- TP08 : RCS-91 et 94 sur plateforme (Ayoub), RCS-92 sur IA (Elias), RCS-93 sur données/benchmark (Omar), RCS-95 sur gouvernance/intégration (Gémima), contribution UX/sécurité d'Aminata. Préparer les contrats d'interface en parallèle ; charge et reprise après inférence réelle autorisée. Aucune dépense ni preuve scientifique présumée.

## 4. Rigueur scientifique et observabilité
- Toujours qualifier explicitement chaque chiffre ou résultat : **mesuré**, **calculé**, **estimé**, **hypothétique** ou **ND** (non disponible).
- Ne jamais présenter un dataset industriel de substitution (ex. AI4I, MIMII DUE) comme de la télémétrie hospitalière réelle.
- **Frontière CodeCarbon** : `src/observability/codecarbon_local.py` mesure uniquement le calcul Python **local** (`local_compute`) ; les appels API LLM distants ont `energy_kwh_status = "ND"`.
