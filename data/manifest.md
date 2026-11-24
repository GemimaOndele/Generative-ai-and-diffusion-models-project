# 📚 Data Manifest — RoboCare Sentinel

> **Statut : gabarit vivant.** Aucune source de télémétrie hospitalière réellement autorisée et validée pour le projet. La famille pilote de dispositifs reste à choisir. Un jeu industriel ou artificiel doit être étiqueté **non médical**. Aucun jeu de données sensible/patient ne doit être versionné sans validation explicite des droits, de la licence, de la confidentialité et du canal de stockage.

## Principes

- Ne pas publier de données privées, de secrets, de rapports hospitaliers non autorisés, de clés, de séries brutes privées ou de données personnelles.
- Distinguer **donnée réelle autorisée**, **donnée publique**, **donnée synthétique** et **donnée simulée**.
- Tout jeu utilisé pour un benchmark doit avoir une origine, une licence, une date d'accès et une séparation train/dev/test ou cas gelés documentée.
- Référencer une [dataset card](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/4) par version et un manifeste par expérience, avec unités et traitement des valeurs manquantes.
- Lien : [RCS-40 — contrat de données](https://gemimakerenondelepourou.atlassian.net/browse/RCS-40).

## Sources candidates à examiner

Sans supposer l'autorisation ou la validité :

- UCI **AI4I** : données de maintenance industrielle tabulaire artificielle, pas des capteurs médicaux.
- **MIMII DUE** : anomalies acoustiques de machines industrielles, pas d'équipements biomédicaux.
- openFDA MAUDE / rappels : signalements, **pas** des séries temporelles de capteurs.
- AccessGUDID : métadonnées d'identification des dispositifs, **pas** un journal de pannes.
- Documentation technique autorisée : pour RAG, vérifier droits d'accès et licences.

## Jeux de données / artefacts

| ID | Nom | Type | Source / provenance | Licence / droits | Date accès | Contient données sensibles ? | Localisation | Séparation / usage | Statut |
|---|---|---|---|---|---|---:|---|---|---|
| D-001 | `experiments/test_cases.jsonl` | Gabarit vide du socle | Socle commun (PR #1 / `bd1c5d1`) | Interne projet | 2026-11-22 | Non | dépôt Git | Doit rester vide ; utilisé par le test de structure | Socle |
| D-001b | `experiments/tp04_cases.jsonl` | 10 cas pédagogiques TP04 | Proposés par Elias pour TP04/RCS-75 | Interne projet / à confirmer | 2026-11-23 | Non | dépôt Git | T01–T10, démo uniquement ; **pas gelés collectivement** (RCS-81 `pending`, `freeze_commit` vide) | Brouillon |
| D-002 | À sélectionner | Baseline règles/ML | À renseigner | À vérifier | À renseigner | À vérifier | À renseigner | Train/val/test gelé à définir | ND |
| D-003 | À sélectionner | Diffusion J1 | À renseigner | À vérifier | À renseigner | À vérifier | À renseigner | Cas figés J1 | ND |

*Limite commune : industrialisation ≠ validation biomédicale. Les exécutions locales d'Omar sont des vérifications logicielles ; les cas/évaluations RCS-81 ne sont pas gelés collectivement et aucun résultat live n'est publié.*

## Résultats expérimentaux

| ID | Fichier | Lié à | Généré par | Seed/config | Contient données sensibles ? | Statut |
|---|---|---|---|---|---:|---|
| R-TP04-001 | `experiments/results/tp04_demo.*` | RCS-75/RCS-79 | `src/run_benchmark.py --mode demo` (Omar, local Windows/Python 3.12.10) | clients simulés, 10 cas × 4 stratégies | Non | Smoke test orchestration uniquement — **pas** une mesure LLM |
| R-TP04-002 | `experiments/results/tp04_live.*` | RCS-79/RCS-81 | `src/run_benchmark.py --mode live` (non exécuté) | modèles A/B à valider | À vérifier | Non exécuté ; cas RCS-81 non gelés collectivement |
| R-J1-001 | `experiments/results/diffusion_*.csv` | RCS-70/RCS-57 | scripts diffusion | À renseigner | Non | Non exécuté |

## Contrôles avant ajout

- [ ] Origine documentée
- [ ] Licence/droits vérifiés
- [ ] Données sensibles exclues ou anonymisées selon procédure validée
- [ ] Taille compatible Git / sinon stockage externe approuvé
- [ ] Hash ou version du fichier consigné
- [ ] Impact sur reproductibilité documenté
