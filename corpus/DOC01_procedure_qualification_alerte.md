# DOC01 — Procédure RCS de qualification d'une alerte (v1.0, 2026-11-18)
Statut : document interne de l'équipe RoboCare Sentinel, rédigé pour le POC. Les délais sont des hypothèses à valider avec un service biomédical.

Lorsqu'une alerte est créée par la plateforme, elle reçoit le statut « à qualifier ». Le technicien biomédical habilité consulte le score d'anomalie, la qualité des données et l'historique de l'équipement.

Le technicien doit ensuite valider ou rejeter l'alerte et saisir un commentaire justifiant sa décision. La décision est horodatée en UTC et enregistrée dans le journal d'audit avec l'identifiant pseudonymisé du technicien.

Si l'alerte est validée, le technicien peut ouvrir un ticket d'intervention. Une intervention ne peut jamais être ouverte sur une alerte rejetée ou non qualifiée.

La plateforme n'envoie aucune commande à l'équipement médical : aucune action automatique de pilotage, de réparation ou d'arrêt n'est autorisée.

Délai cible (hypothèse projet) : qualification sous 4 heures ouvrées pour un équipement de criticité haute, sous 2 jours ouvrés pour une criticité faible.
