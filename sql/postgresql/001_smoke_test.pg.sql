-- Test de fumée du schéma PostgreSQL 001 (données fictives). Tout est annulé à la fin (ROLLBACK).
-- Usage : psql -d robocare -v ON_ERROR_STOP=1 -f sql/postgresql/001_smoke_test.pg.sql
BEGIN;

INSERT INTO source_donnees VALUES ('S04','AI4I 2020','https://archive.ics.uci.edu/dataset/601','CC BY 4.0','substitut NON médical','2026-11-20');
INSERT INTO lot_import (source_id,fichier,sha256,nb_lignes,nb_acceptees,nb_rejetees,nb_doublons,importe_le)
VALUES ('S04','ai4i2020.csv',repeat('a',64),2,2,0,0,now());
INSERT INTO equipement (id,type,criticite) VALUES ('AI4I-M1','machine fictive','moyenne'),('AI4I-M2','machine fictive','haute');
INSERT INTO observation (equipement_id,lot_id,cle_source,air_temp_k,process_temp_k,rpm,torque_nm,tool_wear_min,label,label_origine)
VALUES ('AI4I-M1',1,'1',298.1,308.6,1551,42.8,0,false,'synthétique (AI4I)'),
       ('AI4I-M2',1,'2',298.2,308.7,1408,46.3,3,true,'synthétique (AI4I)');
INSERT INTO utilisateur VALUES ('U1','tech-01','technicien');
INSERT INTO analyse_modele (observation_id,model_version,score,seuil,cree_le) VALUES (1,'zscore-v1',0.2,0.8,now()),(2,'zscore-v1',0.95,0.8,now());
INSERT INTO alerte (analyse_id,equipement_id,gravite,cree_le) VALUES (2,'AI4I-M2','critique',now());
UPDATE alerte SET statut='validee', decide_par='U1', decide_le=now() WHERE id=1;
INSERT INTO intervention (alerte_id,equipement_id,responsable_id,cree_le) VALUES (1,'AI4I-M2','U1',now());
INSERT INTO experiment_run (jalon,config,seed,commit_sha,cree_le) VALUES ('J1','{"model":"zscore"}',42,'f168a3d',now());
INSERT INTO experiment_metric VALUES (1,'f1',0.5,NULL,'test');

-- Chaque contrainte doit refuser une donnée invalide.
DO $$
DECLARE refus int := 0;
BEGIN
    BEGIN INSERT INTO alerte (analyse_id,equipement_id,gravite,cree_le) VALUES (1,'AI4I-M2','info',now());
    EXCEPTION WHEN raise_exception THEN refus := refus + 1; END;               -- équipement incohérent
    BEGIN UPDATE alerte SET statut='rejetee', decide_par=NULL WHERE id=1;
    EXCEPTION WHEN check_violation THEN refus := refus + 1; END;               -- décision sans acteur
    BEGIN INSERT INTO lot_import (source_id,fichier,sha256,nb_lignes,nb_acceptees,nb_rejetees,nb_doublons,importe_le)
          VALUES ('S04','copie.csv',repeat('a',64),1,1,0,0,now());
    EXCEPTION WHEN unique_violation THEN refus := refus + 1; END;              -- lot déjà importé
    BEGIN UPDATE observation SET equipement_id='AI4I-M1' WHERE id=2;
    EXCEPTION WHEN raise_exception THEN refus := refus + 1; END;               -- observation déplacée
    BEGIN INSERT INTO experiment_metric VALUES (1,'f1',0.6,NULL,'test');
    EXCEPTION WHEN unique_violation THEN refus := refus + 1; END;              -- métrique en double
    IF refus <> 5 THEN RAISE EXCEPTION 'smoke test KO : % refus sur 5', refus; END IF;
    RAISE NOTICE 'smoke test OK : 11 tables alimentées, 5 refus attendus sur 5';
END $$;

ROLLBACK;
