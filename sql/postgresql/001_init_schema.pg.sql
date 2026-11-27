-- RoboCare Sentinel — migration 001, portage PostgreSQL (>= 13) de sql/001_init_schema.sql (SQLite).
-- Même modèle (11 tables, mêmes clés, mêmes contraintes), mêmes noms de colonnes.
-- Différences de portage :
--   * INTEGER PRIMARY KEY AUTOINCREMENT  -> BIGINT GENERATED ALWAYS AS IDENTITY
--   * TEXT horodatage ISO-8601           -> TIMESTAMPTZ ; date_verif -> DATE
--   * REAL                               -> DOUBLE PRECISION
--   * INTEGER 0/1                        -> BOOLEAN (est_fictif, label)
--   * config JSON (texte)                -> JSONB
--   * triggers SQLite RAISE(ABORT)       -> fonctions PL/pgSQL
--   * PRAGMA foreign_keys inutile (FK toujours actives en PostgreSQL)
-- Usage : psql -d robocare -v ON_ERROR_STOP=1 -f sql/postgresql/001_init_schema.pg.sql

BEGIN;

CREATE TABLE IF NOT EXISTS source_donnees (
    id            TEXT PRIMARY KEY,           -- ex. S04
    nom           TEXT NOT NULL,
    url           TEXT NOT NULL,
    licence       TEXT NOT NULL,
    categorie     TEXT NOT NULL,              -- ex. 'substitut NON médical'
    date_verif    DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS lot_import (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id     TEXT NOT NULL REFERENCES source_donnees(id),
    fichier       TEXT NOT NULL,
    sha256        CHAR(64) NOT NULL UNIQUE,   -- idempotence : un même fichier = un seul lot
    nb_lignes     INTEGER NOT NULL CHECK (nb_lignes >= 0),
    nb_acceptees  INTEGER NOT NULL CHECK (nb_acceptees >= 0),
    nb_rejetees   INTEGER NOT NULL CHECK (nb_rejetees >= 0),
    nb_doublons   INTEGER NOT NULL CHECK (nb_doublons >= 0),
    importe_le    TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS equipement (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    modele        TEXT,
    site          TEXT,
    criticite     TEXT CHECK (criticite IN ('faible','moyenne','haute')),
    etat          TEXT NOT NULL DEFAULT 'en_service',
    est_fictif    BOOLEAN NOT NULL DEFAULT TRUE   -- TRUE = équipement fictif / substitut
);

CREATE TABLE IF NOT EXISTS observation (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    lot_id          BIGINT NOT NULL REFERENCES lot_import(id),
    cle_source      TEXT NOT NULL,            -- UDI AI4I
    air_temp_k      DOUBLE PRECISION NOT NULL,
    process_temp_k  DOUBLE PRECISION NOT NULL,
    rpm             DOUBLE PRECISION NOT NULL,
    torque_nm       DOUBLE PRECISION NOT NULL,
    tool_wear_min   DOUBLE PRECISION NOT NULL,
    label           BOOLEAN NOT NULL,
    label_origine   TEXT NOT NULL,            -- 'synthétique (AI4I)'
    UNIQUE (equipement_id, cle_source)        -- déduplication logique
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id            TEXT PRIMARY KEY,
    pseudonyme    TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('technicien','responsable','admin'))
);

CREATE TABLE IF NOT EXISTS analyse_modele (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    observation_id  BIGINT NOT NULL REFERENCES observation(id),
    model_version   TEXT NOT NULL,
    score           DOUBLE PRECISION NOT NULL,
    seuil           DOUBLE PRECISION NOT NULL,
    cree_le         TIMESTAMPTZ NOT NULL,
    UNIQUE (observation_id, model_version)
);

CREATE TABLE IF NOT EXISTS alerte (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analyse_id      BIGINT NOT NULL UNIQUE REFERENCES analyse_modele(id),  -- 1 analyse => au plus 1 alerte
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    gravite         TEXT NOT NULL CHECK (gravite IN ('info','attention','critique')),
    statut          TEXT NOT NULL DEFAULT 'a_qualifier'
                    CHECK (statut IN ('a_qualifier','validee','rejetee')),
    decide_par      TEXT REFERENCES utilisateur(id),
    decide_le       TIMESTAMPTZ,
    commentaire     TEXT,
    cree_le         TIMESTAMPTZ NOT NULL,
    CHECK (statut = 'a_qualifier' OR (decide_par IS NOT NULL AND decide_le IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS intervention (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alerte_id       BIGINT REFERENCES alerte(id),
    equipement_id   TEXT NOT NULL REFERENCES equipement(id),
    responsable_id  TEXT NOT NULL REFERENCES utilisateur(id),
    statut          TEXT NOT NULL DEFAULT 'ouverte' CHECK (statut IN ('ouverte','en_cours','cloturee')),
    compte_rendu    TEXT,
    cree_le         TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    acteur      TEXT NOT NULL,
    evenement   TEXT NOT NULL,
    cible       TEXT NOT NULL,
    horodatage  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_run (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    jalon       TEXT NOT NULL CHECK (jalon IN ('J1','J2')),
    config      JSONB NOT NULL,
    seed        INTEGER,
    materiel    TEXT,
    commit_sha  TEXT,
    cree_le     TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_metric (
    run_id   BIGINT NOT NULL REFERENCES experiment_run(id),
    nom      TEXT NOT NULL,
    valeur   DOUBLE PRECISION,
    unite    TEXT,
    split    TEXT NOT NULL,
    PRIMARY KEY (run_id, nom, split)
);

CREATE INDEX IF NOT EXISTS idx_obs_equipement ON observation(equipement_id);
CREATE INDEX IF NOT EXISTS idx_alerte_statut  ON alerte(statut);

-- Cohérence alerte / observation : l'alerte porte sur l'équipement de l'observation analysée.
CREATE OR REPLACE FUNCTION rcs_check_alerte_equipement() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM analyse_modele a JOIN observation o ON o.id = a.observation_id
        WHERE a.id = NEW.analyse_id AND o.equipement_id = NEW.equipement_id
    ) THEN
        RAISE EXCEPTION 'alert equipment mismatch';
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS alert_equipment_check ON alerte;
CREATE TRIGGER alert_equipment_check
BEFORE INSERT OR UPDATE OF analyse_id, equipement_id ON alerte
FOR EACH ROW EXECUTE FUNCTION rcs_check_alerte_equipement();

CREATE OR REPLACE FUNCTION rcs_check_analyse_equipement() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM alerte a JOIN observation o ON o.id = NEW.observation_id
        WHERE a.analyse_id = OLD.id AND a.equipement_id <> o.equipement_id
    ) THEN
        RAISE EXCEPTION 'analysis equipment mismatch';
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS analysis_equipment_update ON analyse_modele;
CREATE TRIGGER analysis_equipment_update
BEFORE UPDATE OF observation_id ON analyse_modele
FOR EACH ROW EXECUTE FUNCTION rcs_check_analyse_equipement();

CREATE OR REPLACE FUNCTION rcs_check_observation_equipement() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM analyse_modele m JOIN alerte a ON a.analyse_id = m.id
        WHERE m.observation_id = OLD.id AND a.equipement_id <> NEW.equipement_id
    ) THEN
        RAISE EXCEPTION 'observation equipment mismatch';
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS observation_equipment_update ON observation;
CREATE TRIGGER observation_equipment_update
BEFORE UPDATE OF equipement_id ON observation
FOR EACH ROW EXECUTE FUNCTION rcs_check_observation_equipement();

COMMIT;
