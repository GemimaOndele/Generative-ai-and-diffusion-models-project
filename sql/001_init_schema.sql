-- RoboCare Sentinel — migration 001 : schéma initial (SQLite). MLD : docs/26_rcs42_mld_sql.md (RCS-41/42)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_donnees (
    id            TEXT PRIMARY KEY,           -- ex. S04
    nom           TEXT NOT NULL,
    url           TEXT NOT NULL,
    licence       TEXT NOT NULL,
    categorie     TEXT NOT NULL,              -- ex. 'substitut NON médical'
    date_verif    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lot_import (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id     TEXT NOT NULL REFERENCES source_donnees(id),
    fichier       TEXT NOT NULL,
    sha256        TEXT NOT NULL UNIQUE,       -- idempotence : un même fichier = un seul lot
    nb_lignes     INTEGER NOT NULL,
    nb_acceptees  INTEGER NOT NULL,
    nb_rejetees   INTEGER NOT NULL,
    nb_doublons   INTEGER NOT NULL,
    importe_le    TEXT NOT NULL               -- UTC ISO-8601
);

CREATE TABLE IF NOT EXISTS equipement (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    modele        TEXT,
    site          TEXT,
    criticite     TEXT CHECK (criticite IN ('faible','moyenne','haute')),
    etat          TEXT NOT NULL DEFAULT 'en_service',
    est_fictif    INTEGER NOT NULL DEFAULT 1  -- 1 = équipement fictif / substitut
);

CREATE TABLE IF NOT EXISTS observation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    lot_id          INTEGER NOT NULL REFERENCES lot_import(id),
    cle_source      TEXT NOT NULL,            -- UDI AI4I
    air_temp_k      REAL NOT NULL,
    process_temp_k  REAL NOT NULL,
    rpm             REAL NOT NULL,
    torque_nm       REAL NOT NULL,
    tool_wear_min   REAL NOT NULL,
    label           INTEGER NOT NULL CHECK (label IN (0,1)),
    label_origine   TEXT NOT NULL,            -- 'synthétique (AI4I)'
    UNIQUE (equipement_id, cle_source)        -- déduplication logique
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id            TEXT PRIMARY KEY,
    pseudonyme    TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('technicien','responsable','admin'))
);

CREATE TABLE IF NOT EXISTS analyse_modele (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id  INTEGER NOT NULL REFERENCES observation(id),
    model_version   TEXT NOT NULL,
    score           REAL NOT NULL,
    seuil           REAL NOT NULL,
    cree_le         TEXT NOT NULL,
    UNIQUE (observation_id, model_version)
);

CREATE TABLE IF NOT EXISTS alerte (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    analyse_id      INTEGER NOT NULL UNIQUE REFERENCES analyse_modele(id),  -- 1 analyse => au plus 1 alerte
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    gravite         TEXT NOT NULL CHECK (gravite IN ('info','attention','critique')),
    statut          TEXT NOT NULL DEFAULT 'a_qualifier'
                    CHECK (statut IN ('a_qualifier','validee','rejetee')),
    decide_par      TEXT REFERENCES utilisateur(id),
    decide_le       TEXT,
    commentaire     TEXT,
    cree_le         TEXT NOT NULL,
    CHECK (statut = 'a_qualifier' OR (decide_par IS NOT NULL AND decide_le IS NOT NULL AND length(trim(decide_le)) > 0))
);

CREATE TABLE IF NOT EXISTS intervention (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alerte_id       INTEGER REFERENCES alerte(id),
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    responsable_id  TEXT NOT NULL REFERENCES utilisateur(id),
    statut          TEXT NOT NULL DEFAULT 'ouverte' CHECK (statut IN ('ouverte','en_cours','cloturee')),
    compte_rendu    TEXT,
    cree_le         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    acteur      TEXT NOT NULL,
    evenement   TEXT NOT NULL,
    cible       TEXT NOT NULL,
    horodatage  TEXT NOT NULL
);

-- Couche scientifique
CREATE TABLE IF NOT EXISTS experiment_run (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    jalon       TEXT NOT NULL CHECK (jalon IN ('J1','J2')),
    config      TEXT NOT NULL,     -- JSON
    seed        INTEGER,
    materiel    TEXT,
    commit_sha  TEXT,
    cree_le     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_metric (
    run_id   INTEGER NOT NULL REFERENCES experiment_run(id),
    nom      TEXT NOT NULL,
    valeur   REAL,
    unite    TEXT,
    split    TEXT NOT NULL,
    PRIMARY KEY (run_id, nom, split)
);

CREATE INDEX IF NOT EXISTS idx_obs_equipement ON observation(equipement_id);
CREATE INDEX IF NOT EXISTS idx_alerte_statut ON alerte(statut);

-- Integrity across the analysis/observation/alert chain (including later changes).
CREATE TRIGGER IF NOT EXISTS alert_equipment_insert
BEFORE INSERT ON alerte
WHEN NOT EXISTS (SELECT 1 FROM analyse_modele a JOIN observation o ON o.id=a.observation_id WHERE a.id=NEW.analyse_id AND o.equipement_id=NEW.equipement_id)
BEGIN SELECT RAISE(ABORT, 'alert equipment mismatch'); END;
CREATE TRIGGER IF NOT EXISTS alert_equipment_update
BEFORE UPDATE OF analyse_id, equipement_id ON alerte
WHEN NOT EXISTS (SELECT 1 FROM analyse_modele a JOIN observation o ON o.id=a.observation_id WHERE a.id=NEW.analyse_id AND o.equipement_id=NEW.equipement_id)
BEGIN SELECT RAISE(ABORT, 'alert equipment mismatch'); END;
CREATE TRIGGER IF NOT EXISTS analysis_equipment_update
BEFORE UPDATE OF observation_id ON analyse_modele
WHEN EXISTS (SELECT 1 FROM alerte a JOIN observation o ON o.id=NEW.observation_id WHERE a.analyse_id=OLD.id AND a.equipement_id<>o.equipement_id)
BEGIN SELECT RAISE(ABORT, 'analysis equipment mismatch'); END;
CREATE TRIGGER IF NOT EXISTS observation_equipment_update
BEFORE UPDATE OF equipement_id ON observation
WHEN EXISTS (SELECT 1 FROM analyse_modele m JOIN alerte a ON a.analyse_id=m.id WHERE m.observation_id=OLD.id AND a.equipement_id<>NEW.equipement_id)
BEGIN SELECT RAISE(ABORT, 'observation equipment mismatch'); END;
