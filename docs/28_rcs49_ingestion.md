# RCS-49 — Ingestion CSV avec validations

Pilote : Omar · binôme : Ayoub · relecteur : Elias. Code : `src/rcs/ingestion.py` ; contrat : RCS-40
(`docs/24_rcs40_dictionnaire_contrat_donnees.md`) ; stockage : `src/rcs/db.py` + `sql/` (RCS-42/50).

## Ce qui est implémenté

| Exigence du ticket | Implémentation | Test |
|---|---|---|
| Schéma | colonnes obligatoires ; lot entier rejeté si colonne manquante | `test_missing_columns_rejected` |
| Erreurs | type, plage physique, domaine `Type`, cohérence `process ≥ air` → ligne en quarantaine (`data/quarantine/*.jsonl`) | `test_import_accepts_rejects_and_dedups` |
| Doublons | unicité (équipement, clé source) dans le lot et entre lots | `test_overlapping_file_does_not_duplicate_observations` |
| Deux imports identiques | empreinte SHA-256 du fichier : 2ᵉ import = `deja_importe`, aucune nouvelle observation ni lot (audit de rejeu conservé) | `test_same_file_twice_is_idempotent` |
| Logs / provenance | `lot_import` (source, fichier, sha256, compteurs, UTC) + `audit` + manifeste JSON | `data/manifests/ai4i_import.json` |

## Exécution réelle sur AI4I (2026-11-20)

`python scripts/download_ai4i.py` (vérifie le SHA-256) puis import : **10 000 lignes acceptées, 0 rejet, 0 doublon** ;
2ᵉ import du même fichier : **ignoré (idempotent)** — voir `data/manifests/ai4i_import.json`.

## Limites

Ingestion **API** (openFDA) non implémentée : seule l'entrée CSV est couverte (fichier local ou upload). Les données
brutes restent hors Git (`data/raw/` ignoré) ; AI4I est un substitut **non médical**.


La quarantaine est persistée avant l'insertion du lot ; par défaut elle est hors dépôt dans ~/.local/share/robocare_sentinel/quarantine, configurable par RCS_QUARANTINE_DIR ou quarantine_dir. Les valeurs NaN/Inf sont rejetées. Une erreur d'écriture bloque l'import. Ne jamais placer la quarantaine contenant les rejets bruts dans Git. L'API openFDA reste explicitement hors périmètre de cette livraison CSV.
