# RoboCare Sentinel — Cadrage après revue pédagogique et TP08
**Date : 24/11/2026. Statut : proposition d'évolution à ratifier.** Sources : restitution de la revue du 23/11 ; TP08 ECE, 23/11/2026, p.1–6. Le document n'atteste ni approbation du professeur ni résultats d'exécution.
## Périmètre métier
Maintenance des équipements biomédicaux, pas robotique logistique hospitalière. Catalogue candidat : pompes à perfusion, respirateurs/ventilateurs, incubateurs néonatals, hémodialyse, radiographie, CT, IRM, échographie, moniteurs. DEC-02 demeure ouverte. J1 : génération/reconstruction par diffusion pour plusieurs familles si données compatibles, comparaison indépendante à une baseline. J2 : assistant documentaire Multi-LLM sur sous-ensemble de familles et corpus autorisés, avec citations, abstention, validation humaine. La prédiction de panne repose sur modèles spécialisés et données temporelles adéquates, pas sur une réponse LLM seule.
## Vues d'architecture à documenter
| Vue | Cible proposée | Preuve/limite |
|---|---|---|
| Métier | AS IS / TO BE, BPMN, technicien, responsable, escalade | RCS-20/21/30/31 |
| Fonctionnelle | inventaire, mesures, alertes, interventions, assistant, coûts/Green AI | RCS-38/39/44/54/60 |
| Applicative | navigateur → API authentifiée → services données/IA → stockage | RCS-43 ; PR #31 locale fictive, non fusionnée |
| Données | Bronze brut autorisé → Silver contrôlé → Gold analytique | RCS-40/41/42/49/50 ; SQLite POC, PostgreSQL + stockage objet à comparer |
| IA | J1 baseline/diffusion ; J2 retrieval + modèles A/B + validation | RCS-69/74/75/81 ; modèles et cas non gelés collectivement |
| Déploiement | API loopback, moteur sur réseau privé ; local CPU prioritaire à évaluer | RCS-91/92 ; aucun déploiement TP08 prouvé |
| Sécurité | secrets hors Git, accès minimal, refus données non autorisées | RCS-66/84 ; aucune commande machine |
| Exploitation | traces, health/readiness, charge, incidents, coûts | RCS-78/89/90/93/94/95 |
## Contrat de données et monitoring
Séparer état de fonctionnement, criticité, score/confiance, validation du technicien, workflow. Vert : normal documenté ; orange : anomalie à examiner ; rouge : critique selon règle métier validée ; gris : inconnu/incomplet. Orange ne garantit jamais la sécurité de fonctionnement. Stocker provenance, unité, identifiant équipement, timestamp UTC seulement s'il existe, fenêtre/séquence, étiquette et source de vérité. Ne pas utiliser UDI AI4I comme temps. Modalités candidates texte, mesures, images, audio, vidéo ; aucune modalité médicale brute confirmée dans les archives. MAUDE/rappels = événements documentaires, AccessGUDID = métadonnées ; AI4I/MIMII DUE = substituts non médicaux. Pas de taux de panne déduit du volume de rapports.
## Architecture médaillon proposée
Bronze : fichiers immuables + empreinte et droits. Silver : contrôle qualité, quarantaine, normalisation unités/temps, déduplication, métadonnées et labels sourcés. Gold : splits versionnés, agrégats et preuves, alertes candidates. Stockage relationnel des métadonnées et interventions ; fichiers volumineux hors Git en stockage objet autorisé ; séries temporelles et vectorisation seulement après besoin démontré. SQLite reste support de tests, pas choix définitif. Aucun accès patient ni commande réseau aux dispositifs.
## TP08 — passage du POC au déploiement contrôlé
| Ticket | Critère / preuve |
|---|---|
| RCS-91 | docs/deployment_decision.md : schéma local/cloud, frontières, SLO proposés, coût |
| RCS-92 | /healthz, /readyz, /v1/generate ; vraie réponse, modèle, trace_id ; evidence/smoke.json sans prompt |
| RCS-93 | hypothèse fixée avant mesure ; 2 paliers minimum sur propre service, CSV/JSON, N, succès, erreurs, latence et débit |
| RCS-94 | panne contrôlée backend uniquement sur environnement propre ; readiness 503 attendue, reprise et nouvelle inférence ; docs/incident_runbook.md |
| RCS-95 | décision argumentée fonctionnel/sécurité/capacité/fiabilité/économie ; README et hash |
Parcours A recommandé par le TP : Docker Compose + Ollama + FastAPI local CPU. B optionnel GPU vLLM/tunnel SSH si ressource autorisée ; C plan B tests unitaires et blocage honnête. Sans inférence réelle : NO-GO technique ; fuite possible : NO-GO sécurité. Deux petits paliers ne prouvent pas un SLO, aucune énergie déduite de la latence. Décision de production clinique hors périmètre. Coûts : distinguer hypothèses, dépenses, temps humain, maintenance/immobilisation, infrastructure, coût par succès métier et énergie locale estimée. J1 reste distinct.
## Gouvernance
Consolider avant de créer des branches. main et gh-pages permanentes ; branches temporaires supprimables seulement après preuve de fusion/conservation, absence de dépendance ou commits supplémentaires. PR #1 fusionnée bd1c5d1. PR #31 et #32 en revue/dépendance ; PR #8/#22 historiques à fermer sans double merge après validation des remplaçantes. RCS-91–95 déjà présents dans Jira ; aucun ticket doublon à créer, responsables proposés non ratifiés. Fichiers de présentation du 23/11 archivés sans réécriture.
