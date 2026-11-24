# Contrat de traces, rédaction PII et seuils de monitoring — `RCS-89`

> **Statut** : Spécification v1 alignée sur `src/observability/codecarbon_local.py` (PR #3) et le contrat JSON `data/contracts/trace_event_v1.json`.  
> **Frontière environnementale** : CodeCarbon (`tracked_local_run`, `read_local_metrics`) ne mesure que le calcul Python **local** (`boundary = "local_compute"`). Les appels API LLM distants ne sont jamais mesurés par CodeCarbon (`energy_kwh_status = "ND"`).

---

## 1. Contrat de journalisation d'événement (`data/contracts/trace_event_v1.json`)

Chaque exécution d'inférence (Diffusion J1, Orchestrateur Multi-LLM J2, ingestion ou triage) émet un événement JSON structuré respectant strictement `additionalProperties: false`.

| Champ | Type | Obligatoire | Contrainte / Valeurs | Description |
| :--- | :--- | :---: | :--- | :--- |
| `schema_version` | `string` | Oui | `"1.0.0"` | Version du contrat de trace. |
| `timestamp_utc` | `string` | Oui | ISO-8601 UTC (`...Z`) | Horodatage d'émission de l'événement. |
| `trace_id` | `string` | Oui | `^[A-Za-z0-9][A-Za-z0-9_-]{7,63}$` | Identifiant de corrélation bout-en-bout. |
| `run_id` | `string` | Oui | `^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$` | Aligné sur `_storage_path` de `codecarbon_local.py`. |
| `component` | `string` | Oui | `ingestion` \| `diffusion_j1` \| `orchestrator_j2` \| `alerts_hitl` \| `api` | Composant émetteur. |
| `model_version` | `string` | Oui | Non vide (`"none"` si hors modèle) | Version figée du modèle / baseline. |
| `status` | `string` | Oui | `ok` \| `fallback` \| `error` | Issue de l'exécution. |
| `latency_ms` | `number` | Oui | `>= 0` | Latence mesurée en millisecondes. |
| `cost_eur` | `number` \| `null` | Oui | `>= 0` ou `null` | Coût estimé/mesuré en euros (`null` si ND). |
| `energy_kwh` | `number` \| `null` | Oui | `>= 0` ou `null` | Énergie locale en kWh (`null` si `energy_kwh_status == "ND"`). |
| `energy_kwh_status` | `string` | Oui | `measured` \| `estimated` \| `ND` | Statut de preuve énergétique (`estimated` pour CodeCarbon local, `ND` pour API distante). |
| `boundary` | `string` | Oui | `local_compute` \| `remote_api` \| `hybrid` | Frontière d'exécution observée. |
| `fallback_triggered` | `boolean` | Oui | `true` \| `false` | Indique un basculement en repli déterministe. |
| `error_code` | `string` \| `null` | Non | Code court normalisé (sans stacktrace brute) | Code d'erreur technique éventuel. |

---

Pour `ND`, l’énergie est obligatoirement `null` ; pour `measured` ou `estimated`, une valeur numérique non négative est obligatoire. Une frontière `remote_api` ou `hybrid` reste ND dans ce contrat v1 : une mesure locale partielle ne doit pas être assimilée au total distant/hybride.

La projection des traces J2 est portée par la PR #33 (RCS-78), empilée sur ce contrat. Elle utilise une liste fermée de métadonnées et exige la preuve de provenance et du fallback. Les champs bruts `case_id`, `strategy`, `variant`, prompts et réponses ne sont pas copiés. L'intégration reste soumise à la revue et aux tests sur la base consolidée.

## 2. Règles strictes d'absence de données patient et de rédaction PII

1. **Interdiction absolue de données patient (PHI/PII)** : aucun champ d'identité ou de santé patient (`patient_id`, `patient_name`, `ipp`, `nir`, `ssn`, `dob`, `birth_date`, `email`, `phone`, `address`, `diagnosis`, `clinical_note`) ne doit figurer dans un événement de trace.
2. **Schéma fermé (`additionalProperties: false`)** : tout payload contenant un champ non déclaré dans `data/contracts/trace_event_v1.json` est **rejeté** avant écriture.
3. **Absence de prompts ou secrets bruts** : ne jamais journaliser de clés API, jetons, variables `.env`, ou contenus textuels bruts sensibles ; conserver uniquement `trace_id`, `run_id`, codes normalisés et métriques numériques.
4. **Stockage hors Git** : conformément à `codecarbon_local.py`, les fichiers `emissions.csv` et journaux de traces locaux sont écrits hors du dépôt Git (ex. `~/.local/share/robocare_sentinel/`).

---

## 3. Seuils d'alerte de monitoring opérationnel

**Valeurs initiales proposées** : à confirmer par expérimentation, sans portée clinique.

| Indicateur | Fenêtre d'observation | Seuil `attention` (Warning) | Seuil `critique` (Critical) | Action de remédiation |
| :--- | :--- | :--- | :--- | :--- |
| **Latence p95** (`latency_ms`) | Fenêtre glissante 15 min | `> 2 000 ms` (J1) / `> 8 000 ms` (J2) | `> 5 000 ms` (J1) / `> 20 000 ms` (J2) | Vérifier charge locale / timeout orchestrateur (`≤ 30 s`) et basculer en mode léger. |
| **Taux d'erreur** (`status == "error"`) | Fenêtre glissante 15 min (min 20 req.) | `> 2 %` | `> 5 %` | Alerter l'équipe technique, inspecter `error_code` et geler les déploiements. |
| **Taux de fallback** (`fallback_triggered == true`) | Fenêtre glissante 1 h | `> 10 %` | `> 25 %` | Auditer le budget/latence Multi-LLM et vérifier la disponibilité des modèles locaux. |
| **Part `energy_kwh_status == "ND"` (local)** | Par lot / run local | `> 0 %` sur `boundary == "local_compute"` | `100 %` sur 2 runs consécutifs | Vérifier l'installation de `codecarbon` et les droits d'accès capteurs locaux. |
