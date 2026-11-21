# DOC04 — Politique de données et RGPD du POC (v1.0, 2026-11-18)
Aucune donnée de patient ne doit être collectée, stockée ou envoyée dans un prompt de modèle de langage. Les questions contenant un nom de patient, un numéro de sécurité sociale (NIR), un e-mail ou un téléphone sont bloquées et redirigées vers un humain.

Les identifiants d'équipements et d'utilisateurs sont pseudonymisés. Les journaux techniques sont conservés 30 jours (hypothèse à valider) et ne contiennent ni secret ni clé API.

Les données brutes restent hors du dépôt Git ; seuls le code, les manifestes, les empreintes SHA-256 et des exemples licites sont versionnés.

Une analyse d'impact (AIPD) doit être évaluée avec un référent si un traitement de données personnelles à risque devenait nécessaire. Un audit technique ne vaut pas déclaration de conformité au RGPD ou à l'AI Act.
