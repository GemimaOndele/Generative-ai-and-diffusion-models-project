# RCS-40 — Dictionnaire et contrat de données (v1, 2026-11-20)

Pilote : Omar · binôme : Gémima · relectrice : Aminata. Version machine du contrat : `data/contracts/ai4i_v1.json`.

Implémentation du contrôle : `src/rcs/ingestion.py` (branche RCS-49).

## 1. Contrat d'entrée AI4I (lot CSV)

| Colonne source | Colonne cible | Type | Unité | Contrôle | Action si échec |
|---|---|---|---|---|---|
| `UDI` | `cle_source` | int ≥ 1 (source), TEXT décimal (cible SQL) | — | obligatoire, unique par (équipement, clé) | doublon compté, non inséré |
| `Type` | `equipement_id` = `AI4I-{L,M,H}` | str ∈ {L, M, H} (source), préfixe AI4I- en cible | — | domaine fermé | ligne en quarantaine |
| `Air temperature [K]` | `air_temp_k` | float | K | 250 ≤ v ≤ 350 | quarantaine |
| `Process temperature [K]` | `process_temp_k` | float | K | 250 ≤ v ≤ 380 et ≥ `air_temp_k` | quarantaine |
| `Rotational speed [rpm]` | `rpm` | float | tr/min | 0 ≤ v ≤ 5 000 | quarantaine |
| `Torque [Nm]` | `torque_nm` | float | N·m | 0 ≤ v ≤ 200 | quarantaine |
| `Tool wear [min]` | `tool_wear_min` | float | min | 0 ≤ v ≤ 400 | quarantaine |
| `Machine failure` | `label` | int ∈ {0,1} | — | obligatoire | quarantaine |
| — | `label_origine` | str | — | constante `synthétique (AI4I)` | — |

Colonnes manquantes dans l'en-tête → **lot entier rejeté** (`statut = rejete`), audité.

## 2. Règles de lot

- **Idempotence** : empreinte SHA-256 du fichier ; un fichier déjà importé n'écrit rien (`deja_importe`).
- **Traçabilité** : `lot_import` (source, fichier, sha256, compteurs, horodatage UTC) + `audit`.
- **Quarantaine** : `data/quarantine/<fichier>_<sha8>_rejets.jsonl` (ligne, erreur, brut) — hors Git.
- **Manifeste** : `data/manifests/ai4i_import.json` (source, licence, compteurs, erreurs).

## 3. Dictionnaire des attributs standard (cible multi-sources, Bibliothèque §7.4)

| Attribut | Type | Contrôle | Statut POC |
|---|---|---|---|
| `equipment_id` | str pseudonymisé | stable, sans donnée patient | ✔ (`equipement.id`) |
| `captured_at_utc` | ISO-8601 | fuseau, tri, dérive | ✘ AI4I n'a pas d'horodatage — à ajouter pour une vraie télémétrie |
| `signal_name` / `unit` | str | dictionnaire d'unités | ✔ (colonnes typées + unités ci-dessus) |
| `value` / `status` | float / str | plage, manquants | ✔ |
| `source_id` / `batch_id` | str / int | provenance, idempotence | ✔ (`S04`, `lot_import.id`) |
| `event_code` / `report_text` | str | pas d'identifiant patient | prévu pour openFDA (J2) |
| `label` / `label_origin` | int / str | pas de « vérité terrain » supposée | ✔ |

## 4. KPI qualité rapportés sur AI4I (import complet à reproduire)

Ces compteurs sont rapportés par l'auteur, non vérifiés dans cette PR ; le manifeste généré doit être fourni avant validation expérimentale. Reproduire sur la branche pipeline RCS-52 avec le téléchargement vérifié et la commande documentée dans cette branche ; conserver le SHA-256, les compteurs et le commit d'exécution, sans publier les données brutes.

| KPI | Valeur |
|---|---|
| Lignes reçues / acceptées / rejetées / doublons | 10 000 / 10 000 / 0 / 0 |
| Champs requis manquants | 0 % |
| Ratio normal / anomalie | 9 661 / 339 (3,39 %) |
| 2ᵉ import identique | ignoré (idempotent) — testé |

## 5. Manifeste des sources, versions et splits

Découper d'abord la totalité des observations étiquetées en 60/20/20 stratifié (seed 42), puis filtrer les normales uniquement dans le train pour l'entraînement non supervisé. Validation et test restent intacts ; seuils et choix de variantes ne doivent jamais être ajustés sur le test. Le gel effectif des cas nécessite un manifeste versionné.

Règle : les données brutes ne sont **jamais** versionnées (`data/raw/` est ignoré par Git). Le dépôt contient le code,
les empreintes, les manifestes et le corpus documentaire rédigé par l'équipe.

| ID | Jeu | Origine / URL | Licence / droits | Version & empreinte | Usage | Séparation | Limites |
|---|---|---|---|---|---|---|---|
| S04 | AI4I 2020 Predictive Maintenance | UCI — https://archive.ics.uci.edu/dataset/601/ai4i (zip `ai4i+2020+predictive+maintenance+dataset.zip`) | CC BY 4.0 — citer : S. Matzka, *Explainable AI for Predictive Maintenance Applications*, AI4I 2020 | `ai4i2020.csv`, 10 000 lignes, SHA-256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`, téléchargé le 2026-11-20 | J1 baseline + diffusion ; démo pipeline | stratifié 60/20/20 seed 42 ; train = normaux du train (5 797) ; val 2 000 (68 pannes) ; test 2 000 (68 pannes) gelé | **synthétique industriel, NON médical** ; ordre ≠ temporalité ; RNF aléatoire |
| CORPUS | Corpus documentaire J2 (`corpus/DOC01…DOC08`) | rédigé par l'équipe RCS (2026-11-18/20) à partir de la Bibliothèque V3 et des fiches sources publiques | interne au projet, partage libre dans le dépôt | 8 fichiers Markdown versionnés | workload de l'assistant Multi-LLM (TP03/TP04/TP05) | 10 questions candidates ; gel collectif et manifeste à vérifier | contient volontairement une source obsolète (DOC06) et une injection (DOC08) pour les tests ; **aucune donnée patient** |
| S01/S02 | openFDA MAUDE / Recalls | https://open.fda.gov/apis/device/event/ — /recall/ | domaine public US ; conditions API à vérifier | non collecté à ce stade | candidat J2 (typologie d'incidents) | — | textes de signalement, **pas de télémétrie**, pas de taux de panne |
| S05 | MIMII DUE | https://zenodo.org/records/4740355 | CC BY-NC-SA 4.0 | non collecté (volumineux) | option J1 acoustique | — | NON médical |

Modèles tiers téléchargés (cache Hugging Face local, poids hors dépôt) :

| Rôle | Modèle | Révision | Licence |
|---|---|---|---|
| LLM A (économique) | `HuggingFaceTB/SmolLM2-360M-Instruct` | `a10cc15` | Apache-2.0 |
| LLM B (robuste) | `Qwen/Qwen2.5-0.5B-Instruct` | `7ae5576` | Apache-2.0 |

Reproduire : `python scripts/download_ai4i.py` (vérifie l'empreinte) ; les modèles se téléchargent au premier
`python run_benchmark.py --mode local`.

Manifeste d'import machine : `data/manifests/ai4i_import.json` (généré par `scripts/demo_pipeline.py`).


Les tests du contrat utilisent des exemples synthétiques et ne prouvent pas la conformité du pipeline réel ; contrôler la concordance avec RCS-49 et RCS-42 après intégration.
