# RCS-41 — MCD (règles de gestion, entités, associations, cardinalités)

Pilote : Omar · binôme : Gémima · relecteur : Elias. Le MLD et le SQL sont livrés par RCS-42.

⚠ **Reste à faire pour clore le ticket** : reporter ce MCD dans **JMerise**, l'exporter (PNG/PDF) dans `docs/jmerise/` et le faire relire avec les besoins métier.

## 1. Règles de gestion

| RG | Règle |
|---|---|
| RG1 | Une source de données fournit 0..n lots d'import ; un lot provient d'une seule source. |
| RG2 | Un lot est identifié de façon unique par l'empreinte SHA-256 du fichier (idempotence). |
| RG3 | Un lot contient 0..n observations ; une observation appartient à un seul lot. |
| RG4 | Un équipement possède 0..n observations ; une observation concerne un seul équipement ; (équipement, clé source) est unique. |
| RG5 | Une observation est scorée par 0..n analyses, au plus une par version de modèle. |
| RG6 | Une analyse produit 0 ou 1 alerte (si score ≥ seuil) ; une alerte provient d'une seule analyse. |
| RG7 | Une alerte est décidée (validée/rejetée) par 0..1 utilisateur habilité (technicien, responsable). |
| RG8 | Une intervention est ouverte sur une alerte **validée** (ou un incident manuel : alerte nulle) ; une alerte peut donner 0..n interventions. |
| RG9 | Toute action sensible produit une ligne d'audit (acteur, événement, cible, horodatage UTC). |
| RG10 | Une exécution d'expérience (J1/J2) possède 1..n métriques (nom, valeur, unité, split). |

## 2. MCD (notation Merise : cardinalités min,max côté entité)

```
SOURCE_DONNEES (0,n) ── FOURNIT ── (1,1) LOT_IMPORT
LOT_IMPORT     (0,n) ── CONTIENT ── (1,1) OBSERVATION
EQUIPEMENT     (0,n) ── MESURE ──── (1,1) OBSERVATION
OBSERVATION    (0,n) ── SCORE ───── (1,1) ANALYSE_MODELE
ANALYSE_MODELE (0,1) ── PRODUIT ─── (1,1) ALERTE
EQUIPEMENT     (0,n) ── CONCERNE ── (1,1) ALERTE
UTILISATEUR    (0,n) ── DECIDE ──── (0,1) ALERTE         [date, commentaire]
ALERTE         (0,n) ── OUVRE ───── (0,1) INTERVENTION
UTILISATEUR    (0,n) ── RESPONSABLE (1,1) INTERVENTION
EQUIPEMENT     (0,n) ── CIBLE ───── (1,1) INTERVENTION
EXPERIMENT_RUN (1,n) ── MESURE_RUN  (1,1) EXPERIMENT_METRIC
```

Entités et identifiants : SOURCE_DONNEES(**id**, nom, url, licence, catégorie, date_verif) ;
LOT_IMPORT(**id**, fichier, sha256, nb_lignes, nb_acceptées, nb_rejetées, nb_doublons, importé_le) ;
EQUIPEMENT(**id**, type, modèle, site, criticité, état, est_fictif) ;
OBSERVATION(**id**, clé_source, air_temp_k, process_temp_k, rpm, torque_nm, tool_wear_min, label, label_origine) ;
ANALYSE_MODELE(**id**, model_version, score, seuil, créé_le) ; ALERTE(**id**, gravité, statut, créé_le) ;
INTERVENTION(**id**, statut, compte_rendu, créé_le) ; UTILISATEUR(**id**, pseudonyme, rôle) ;
AUDIT(**id**, acteur, événement, cible, horodatage) ; EXPERIMENT_RUN(**id**, jalon, config, seed, matériel, commit, créé_le) ;
EXPERIMENT_METRIC(nom, valeur, unité, split).

AUDIT est volontairement non relié par clé étrangère (journal append-only, la cible est textuelle).
