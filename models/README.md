# 🧠 Modèles et versions IA — RoboCare Sentinel

**Statut : sélection et expériences réelles non validées.** Aucun poids ni modèle hospitalier déployé n'est revendiqué.

| Domaine | Objectif | Points de vigilance |
|---|---|---|
| **J1 diffusion** · RCS-55–59, 69–73 | Modèle entraîné/reconstruction, comparé à des règles/ML | Données sous licence, modalité, train/test indépendant, erreurs, coût |
| **J2 Multi-LLM** · RCS-60–64, 74–80 | Deux vrais LLM A/B et V2 avec RAG, routing ou cascade | Modèles/version/permissions réels, cas gelés, citations, refus |
| **TP05 FinOps/Green/éthique** · RCS-81–85 | Réutiliser J2 avec coût/succès et limites énergétiques/risques | CodeCarbon **local ≠** énergie serveur d'une API distante |
| **Gouvernance** · RCS-87/88 | Model cards, dataset cards, versioning et analyse des biais | Couverture et limites de transfert industriel → biomédical |

Les registres proposés sur [PR #4](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/4) relient **ID modèle, version, fournisseur, licence, dataset/hash, commit, run, métriques, risques et approbation**.

**Aucune performance, empreinte ni conformité réglementaire ne doit être inventée.** Voir [README](../README.md).
