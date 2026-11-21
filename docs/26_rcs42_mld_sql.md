# RCS-42 — MLD, script SQL et tests d'intégrité

Pilote : Omar · binôme : Ayoub · relectrice : Aminata. Dérivé du MCD de RCS-41. Script : `sql/001_init_schema.sql` (appliqué par `src/rcs/db.py`, tracé dans `schema_migrations`). ⚠ SQL écrit à la main : le régénérer depuis JMerise et comparer avant fusion.

## 3. MLD (passage au relationnel)

- source_donnees (**id**, nom, url, licence, categorie, date_verif)
- lot_import (**id**, #source_id, fichier, sha256 *UNIQUE*, nb_lignes, nb_acceptees, nb_rejetees, nb_doublons, importe_le)
- equipement (**id**, type, modele, site, criticite *CHECK*, etat, est_fictif)
- observation (**id**, #equipement_id, #lot_id, cle_source, mesures…, label *CHECK 0/1*, label_origine) *UNIQUE(equipement_id, cle_source)*
- utilisateur (**id**, pseudonyme, role *CHECK*)
- analyse_modele (**id**, #observation_id, model_version, score, seuil, cree_le) *UNIQUE(observation_id, model_version)*
- alerte (**id**, #analyse_id *UNIQUE*, #equipement_id, gravite *CHECK*, statut *CHECK*, #decide_par, decide_le, commentaire, cree_le)
- intervention (**id**, #alerte_id *NULL*, #equipement_id, #responsable_id, statut *CHECK*, compte_rendu, cree_le)
- audit (**id**, acteur, evenement, cible, horodatage)
- experiment_run (**id**, jalon *CHECK J1/J2*, config, seed, materiel, commit_sha, cree_le)
- experiment_metric (**#run_id, nom, split**, valeur, unite)

Index : `idx_obs_equipement(observation.equipement_id)`, `idx_alerte_statut(alerte.statut)` ; les UNIQUE créent leurs
index. Migrations : `sql/NNN_*.sql` appliquées dans l'ordre et tracées dans `schema_migrations`.

## Tests d'intégrité

`test_foreign_keys_enforced`, `test_check_constraints`, `test_migrations_versioned_and_applied_once`,
`test_unique_lot_hash` — `tests/test_rcs42_sql.py`.
