# ⚙️ Backend et contrats API — à implémenter

**État : aucun serveur backend opérationnel confirmé dans `main`.** La PR #1 fournit le cadre du projet, pas une API déjà connectée.

## Périmètre prévu
- Authentification/autorisation des utilisateurs, traçabilité et contrôle d'accès.
- Inventaire et ingestion autorisée, contrôles de qualité, stockage et historiques.
- Exposition des alertes candidates, **validation obligatoire par technicien**.
- Endpoints de consultation des preuves C3/TP04/TP05 et des KPI FinOps/Green AI, **avec provenance et statut de mesure**.
- Budget et quotas de requêtes LLM, timeouts et refus contrôlés (sans boucle illimitée).
- Synchronisation future avec MCD/MLD validé sous **JMerise**.

**À ne pas faire :** connexion à un dispositif médical réel, flux patient, commande autonome, secrets/identifiants dans Git. Avant développement : définir API schema, versions, tests et droits.

Voir [RCS-76 (orchestration)](https://gemimakerenondelepourou.atlassian.net/browse/RCS-76), [RCS-89 (observabilité)](https://gemimakerenondelepourou.atlassian.net/browse/RCS-89) et [README](../README.md).
