# RCS-41 : MLD dérivé du MCD JMerise et comparaison au SQL canonique (#19)

Statut : **dérivation documentaire, à confirmer par l'export MLD de JMerise.** Le MLD ci-dessous applique les règles Merise standard au MCD `docs/jmerise/RCS41_MCD_RoboCare.mcd` (JMerise 0.6.3), tel qu'il apparaît dans l'export `RCS41_MCD_RoboCare.png`. Il sert de grille de contrôle pour l'export « Générer le MLD » de JMerise : chaque ligne doit s'y retrouver à l'identique.

## 0. Contrôle préalable `commit` / `commit_sha` (revue Ayoub du 26/11)

Le binaire `.mcd` contient l'attribut `commit_sha` dans `EXPERIMENT_RUN` (chaîne `commit_sha` présente, aucune chaîne `commit` seule). L'export PNG affiche aussi `commit_sha VARCHAR(40)`. **Aucun réalignement n'est donc nécessaire** : le MCD JMerise utilise déjà le nom canonique de `sql/001_init_schema.sql`.

## 1. Règles de passage appliquées

1. Chaque entité devient une table, et son identifiant devient la clé primaire.
2. Une association binaire (x,n)–(x,1) devient une clé étrangère du côté (x,1). Elle est `NOT NULL` si le minimum vaut 1, et nullable s'il vaut 0.
3. Les attributs portés par une association (x,n)–(0,1) migrent vers la table côté (0,1).
4. Une identification relative (cardinalité entre parenthèses côté entité faible) fait entrer la clé étrangère dans la clé primaire.

## 2. MLD dérivé

Notation : clé primaire en **gras**, clé étrangère préfixée par `#`.

| Table | Colonnes | Association d'origine |
|---|---|---|
| SOURCE_DONNEES | **id_source**, nom, url, licence, categorie, date_verif | — |
| LOT_IMPORT | **id_lot**, #id_source, fichier, sha256, nb_lignes, nb_acceptees, nb_rejetees, nb_doublons, importe_le | FOURNIT (0,n)–(1,1) |
| EQUIPEMENT | **id_equipement**, type, modele, site, criticite, etat, est_fictif | — |
| OBSERVATION | **id_observation**, #id_equipement, #id_lot, cle_source, air_temp_k, process_temp_k, rpm, torque_nm, tool_wear_min, label, label_origine | MESURE (0,n)–(1,1), CONTIENT (0,n)–(1,1) |
| UTILISATEUR | **id_utilisateur**, pseudonyme, role | — |
| ANALYSE_MODELE | **id_analyse**, #id_observation, model_version, score, seuil, cree_le | SCORE (0,n)–(1,1) |
| ALERTE | **id_alerte**, #id_analyse, #id_equipement, #id_utilisateur (nullable), gravite, statut, decide_le, commentaire, cree_le | PRODUIT (0,1)–(1,1), CONCERNE (0,n)–(1,1), DECIDE (0,n)–(0,1) avec ses attributs |
| INTERVENTION | **id_intervention**, #id_alerte (nullable), #id_equipement, #id_utilisateur, statut, compte_rendu, cree_le | OUVRE (0,n)–(0,1), CIBLE (0,n)–(1,1), RESPONSABLE (0,n)–(1,1) |
| AUDIT | **id_audit**, acteur, evenement, cible, horodatage | — |
| EXPERIMENT_RUN | **id_run**, jalon, config, seed, materiel, commit_sha, cree_le | — |
| EXPERIMENT_METRIC | **#id_run, nom, split**, valeur, unite | EVALUE (1,n)–((1,1)) identification relative |

## 3. Comparaison au SQL canonique `sql/001_init_schema.sql`

| Table | Clés et FK du MLD dérivé | SQL canonique | Verdict |
|---|---|---|---|
| source_donnees | PK id_source | `id TEXT PRIMARY KEY` | Conforme (renommage `id_source` → `id`) |
| lot_import | FK id_source NOT NULL | `source_id NOT NULL REFERENCES source_donnees` + `sha256 UNIQUE` | Conforme ; l'unicité de `sha256` (idempotence) est une contrainte physique en plus |
| equipement | PK id_equipement | `id TEXT PRIMARY KEY`, `CHECK criticite`, `est_fictif DEFAULT 1` | Conforme ; les domaines sont des CHECK physiques |
| observation | FK id_equipement, id_lot NOT NULL | les deux FK NOT NULL + `UNIQUE(equipement_id, cle_source)` | Conforme ; la déduplication logique est une contrainte physique en plus |
| utilisateur | PK id_utilisateur | `id TEXT PRIMARY KEY`, `CHECK role` | Conforme |
| analyse_modele | FK id_observation NOT NULL | FK NOT NULL + `UNIQUE(observation_id, model_version)` | Conforme ; l'unicité par version de modèle est un ajout physique |
| alerte | FK id_analyse NOT NULL (côté 1,1) et unique (côté 0,1) ; FK id_equipement NOT NULL ; FK utilisateur nullable + decide_le, commentaire | `analyse_id NOT NULL UNIQUE`, `equipement_id NOT NULL`, `decide_par` nullable, `decide_le`, `commentaire` | Conforme. La règle « décision terminale = acteur + date » est un CHECK SQL ; la cohérence alerte/observation sur l'équipement est assurée par 4 triggers |
| intervention | FK id_alerte nullable, id_equipement NOT NULL, id_utilisateur NOT NULL | `alerte_id` nullable, `equipement_id NOT NULL`, `responsable_id NOT NULL` | Conforme |
| audit | aucune FK | aucune FK | Conforme |
| experiment_run | PK id_run, commit_sha | `id`, `commit_sha TEXT`, `CHECK jalon IN ('J1','J2')` | Conforme |
| experiment_metric | PK (id_run, nom, split) | `PRIMARY KEY (run_id, nom, split)` | Conforme |

**Bilan : 11 tables, 11 clés étrangères, toutes présentes dans le SQL avec la même optionalité.** Aucun écart structurel.

## 4. Écarts conceptuel / physique (déjà documentés, conservés)

| Écart | MCD | SQL | Justification |
|---|---|---|---|
| Run sans métrique | EVALUE (1,n) côté run | un run peut exister sans métrique | Le run est créé avant que ses métriques soient calculées ; (1,n) s'applique à la clôture du run |
| Intervention manuelle | OUVRE (0,1) côté intervention : intervention sans alerte possible | `alerte_id` nullable | Concept cible, pas encore exposé par l'API RCS-50 |
| Audit append-only | règle de gestion | aucune garantie SQL (pas de trigger anti-UPDATE/DELETE) | Convention applicative ; un trigger pourra l'imposer en v2 |
| Types | VARCHAR(n), DECIMAL, BOOLEAN, DATETIME | TEXT, REAL, INTEGER 0/1 + CHECK, TEXT ISO-8601 | Affinités de types SQLite ; les longueurs VARCHAR ne sont pas imposées par SQLite |
| Nommage | `id_<entité>` | `id`, `<table>_id` | Convention SQL du projet |

## 5. Ce qui reste à faire par un humain

1. Ouvrir le `.mcd` dans JMerise 0.6.3 et lancer « Générer le MLD ». Vérifier que l'export correspond aux sections 2 et 3, puis le joindre à `docs/jmerise/` (MLD en PNG et, si JMerise le propose, SQL généré).
2. Contrôle visuel des cardinalités (Elias), à consigner ici avec la date et la version de JMerise.
