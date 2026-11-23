# Règles d'automatisation et contrôle humain (HITL) — `RCS-39`

> **Statut** : Spécification v1 alignée sur `src/rcs/ingestion.py` (PR #12), `src/rcs/alerts.py` et `sql/001_init_schema.sql` (PR #20).  
> **Principe directeur** : Aide à la décision pour la maintenance prédictive des pompes à perfusion. **Aucune action autonome sur un appareil médical réel** n'est autorisée ; toute décision opérationnelle requiert une validation humaine (HITL) tracée dans `audit`.

---

## 1. Périmètre et contrats de référence

| Composant | Fichier / PR | Fonctions & contraintes clés |
| :--- | :--- | :--- |
| **Ingestion déterministe** | `src/rcs/ingestion.py` (PR #12) | `sha256_file`, `validate_row`, `import_csv`, `write_manifest`, `ImportReport`, `ALLOWED_TYPES` (`L`, `M`, `H`) |
| **Persistance & intégrité** | `sql/001_init_schema.sql` (PR #19/#20) | `lot_import(sha256 UNIQUE)`, `observation(UNIQUE(equipement_id, cle_source))`, `analyse_modele(UNIQUE(observation_id, model_version))`, `alerte(analyse_id UNIQUE)`, `intervention`, `audit` |
| **Alertes & revue humaine** | `src/rcs/alerts.py` (PR #20) | `gravite`, `enregistrer_analyse`, `decider_alerte`, `ouvrir_intervention`, `ROLES_HABILITES` (`technicien`, `responsable`), `PermissionRefusee`, `TransitionInvalide` |

---

## 2. Matrice Déclencheurs / Actions / Exceptions (`AUTO-01` à `AUTO-08`)

| ID | Domaine | Déclencheur (Trigger) | Action automatisée / encadrée | Exceptions, bornes & repli (Fallback) | Tables / Fonctions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUTO-01** | **Ingestion déterministe** | Dépôt d'un fichier CSV de télémétrie | Calculer l'empreinte via `sha256_file`, valider chaque ligne avec `validate_row` selon le contrat (`air_temp_k`, `process_temp_k`, `rpm`, `torque_nm`, `tool_wear_min`, `label`, `ALLOWED_TYPES`), insérer les lignes valides et écrire le manifeste via `write_manifest`. | Ligne invalide → rejetée en quarantaine (`quarantine_dir`), compteur `nb_rejetees` incrémenté, sans bloquer les lignes valides. | `import_csv`, `validate_row`, `lot_import`, `observation` |
| **AUTO-02** | **Idempotence SHA-256** | Ré-import d'un fichier CSV déjà traité ou d'une observation déjà connue | Rejeter silencieusement le doublon de lot grâce à `lot_import.sha256 UNIQUE` et ignorer les doublons d'observations via `UNIQUE(equipement_id, cle_source)` (`nb_doublons`). | Fichier modifié avec le même nom → nouveau `sha256`, nouveau `lot_import`, seules les nouvelles paires `(equipement_id, cle_source)` sont insérées. | `sha256_file`, `lot_import`, `observation` |
| **AUTO-03** | **Déduplication d'alertes** | Fin d'une inférence modèle (`score`, `seuil`, `model_version`) sur une `observation_id` | Appeler `enregistrer_analyse` (`INSERT OR IGNORE INTO analyse_modele`) ; si `score >= seuil`, calculer `gravite(score, seuil)` (`critique` si `score >= 2 * seuil`, `attention` si `score >= seuil`, sinon `info`) et créer au plus une alerte (`INSERT OR IGNORE INTO alerte`, `statut = 'a_qualifier'`). | Rejeu de la même `(observation_id, model_version)` → aucune alerte dupliquée (`analyse_id UNIQUE`). `score < seuil` → aucune alerte créée. | `enregistrer_analyse`, `gravite`, `analyse_modele`, `alerte` |
| **AUTO-04** | **Bornes de retries & timeouts** | Appel d'un moteur IA (Diffusion / Multi-LLM) ou d'une dépendance externe | Appliquer des bornes strictes : **max 2 retries** avec backoff exponentiel borné, **timeout ≤ 30 s** par appel modèle, et plafond de budget/tokens par tâche. | Dépassement de timeout, échec après retries ou dépassement de budget → bascule immédiate en repli déterministe (score baseline seul) + journalisation dans `audit` + revue humaine directe. | `src/orchestrator.py`, `audit` |
| **AUTO-05** | **Contrôle d'accès HITL (RBAC)** | Tentative de décision sur une alerte ou d'ouverture d'intervention par un `user_id` | Vérifier que `utilisateur.role` appartient à `ROLES_HABILITES` (`technicien` ou `responsable`). | Rôle non habilité (ex. `admin` non habilité métier ou utilisateur inconnu) → journalisation `decision_refusee_permission` dans `audit` et levée de `PermissionRefusee`. | `decider_alerte`, `ouvrir_intervention`, `utilisateur`, `audit` |
| **AUTO-06** | **Validation / rejet HITL** | Revue d'une alerte au statut `a_qualifier` par un technicien/responsable habilité | Exécuter `decider_alerte` avec `decision` dans `{'validee', 'rejetee'}` et `commentaire` ; renseigner `decide_par`, `decide_le` (UTC ISO-8601) et tracer `alerte_validee` ou `alerte_rejetee` dans `audit`. | Alerte absente → `KeyError`. Statut différent de `a_qualifier` → `TransitionInvalide`. Décision hors `{'validee', 'rejetee'}` → `ValueError`. | `decider_alerte`, `alerte`, `audit` |
| **AUTO-07** | **Ouverture d'intervention encadrée** | Demande d'ouverture d'une fiche d'intervention sur une alerte | Exécuter `ouvrir_intervention` uniquement si `alerte.statut == 'validee'` et `user_id` habilité ; créer la ligne `intervention` (`statut = 'ouverte'`) et tracer `intervention_ouverte` dans `audit`. | Alerte `a_qualifier`, `rejetee` ou inexistante → `TransitionInvalide`. Utilisateur non habilité → `PermissionRefusee`. | `ouvrir_intervention`, `intervention`, `audit` |
| **AUTO-08** | **Garde-fou sécurité clinique** | Toute alerte `critique` ou recommandation générée par LLM | Afficher l'alerte et la recommandation comme **brouillon d'aide à la décision** uniquement ; exiger une action humaine explicite avant toute opération terrain. | **Interdiction absolue** d'envoyer une commande réseau/matérielle vers une pompe à perfusion réelle. Toute tentative hors périmètre est bloquée et auditée. | `alerte`, `intervention`, `audit` |

---

## 3. Cycle de vie des statuts et piste d'audit

### Machine à états des alertes (`alerte.statut`)
* État initial : `a_qualifier` (créé automatiquement par `enregistrer_analyse` lorsque `score >= seuil`).
* Transitions autorisées (uniquement via `decider_alerte` par `ROLES_HABILITES`) :
  * `a_qualifier` → `validee` (événement `audit` : `alerte_validee`)
  * `a_qualifier` → `rejetee` (événement `audit` : `alerte_rejetee`)
* États terminaux : `validee` et `rejetee` (toute nouvelle transition lève `TransitionInvalide`).

### Machine à états des interventions (`intervention.statut`)
* Création uniquement depuis une alerte `validee` via `ouvrir_intervention` → statut initial `ouverte` (événement `audit` : `intervention_ouverte`).
* Progression humaine : `ouverte` → `en_cours` → `cloturee` avec `compte_rendu`.

### Piste d'audit minimale (`audit`)
Chaque événement critique enregistre `(acteur, evenement, cible, horodatage)` en UTC ISO-8601 :
* `decision_refusee_permission`
* `alerte_validee`
* `alerte_rejetee`
* `intervention_ouverte`
