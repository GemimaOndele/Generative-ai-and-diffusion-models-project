# RCS-70 — Manifeste de diffusion (contrôles structurels)

> Décision : **A_TESTER**. Les indices textuels ne prouvent pas un entraînement ; les artefacts fournis restent des déclarations non authentifiées.

## Chaîne à vérifier par exécution

- `q_sample` / bruit gaussien puis prédiction de `epsilon` par un MLP entraîné ;
- échantillonneur inverse DDPM (`sample`) à exécuter ;
- seuil fixé sur validation indépendante, détection comparée à une baseline MAD ;
- seed, versions, hash du jeu et temps d'entraînement consignés dans l'artefact si fourni.

## Preuves (ND tant qu'un artefact réel n'est pas fourni)

| Champ | Valeur |
|---|---|
| seed | ND |
| numpy_version | ND |
| diffusion_timesteps | ND |
| train_updates | ND |
| dataset_sha256 | ND |
| training_runtime_seconds | ND |
| generated_samples_count | ND |
| sample_finite | ND |
| scope | ND |
| scientific_status | ND |
| training_method | ND |
| train_loss_start | ND |
| train_loss_end | ND |

| Métrique synthétique (uniquement si artefact fourni) | Valeur |
|---|---|
| baseline_MAD | ND |
| learned_diffusion_denoiser | ND |

## Contrôles

| Contrôle | Résultat |
|---|---|
| indices_textuels_train | OK |
| indices_textuels_sampler | OK |
| seed_explicite | OK |
| indices_textuels_reverse | OK |
| structure_textuelle_presente | OK |
| artefact_present | ÉCHEC / ND |
| schema_artefact_strict | OK |
| artefact_complet | ÉCHEC / ND |
| perimetre_synthetique_declare | ÉCHEC / ND |
| champs_exportes_autorises | OK |

**Statut de preuve : ND — décision : A_TESTER.**

## Bloquants avant clôture du ticket

- Jeu C3 non gelé collectivement (RCS-69/RCS-81) : aucune comparaison validée.
- Source de données autorisée et licence à vérifier avant tout transfert.
- Le démonstrateur porte sur des signaux synthétiques, sans dispositif ni patient.
- Artefact d'exécution à fournir par un humain : aucun résultat n'est généré ici.

## Reproduction

```bash
python -m tools.rcs70_diffusion_proof --write
python -m tools.rcs70_diffusion_proof --artifact <artefact.json> --write
python -m tools.rcs70_diffusion_proof --check
python -m experiments.rcs69_diffusion_numpy --seed 42 --updates 250 --json <artefact.json>
python -m unittest tests.test_rcs70_diffusion_proof -v
```

Références : PR #7 (`ccabf36`), `docs/19_rcs69_diffusion_numpy_poc.md`, `docs/16_rcs69_preparation_preuve_c3.md`, ADR-008, tickets RCS-69/RCS-70/RCS-81.
