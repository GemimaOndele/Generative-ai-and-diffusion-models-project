# 🛡️ Security & responsible use — RoboCare Sentinel

**Projet académique public, non validé pour un usage médical.** Aucun diagnostic, contrôle d'équipement, décision clinique ou commande machine ne doit être réalisé avec ce code.

## Signaler une vulnérabilité ou une exposition potentielle

Éviter d'ouvrir une issue GitHub **publique** contenant des secrets, des données de santé, des identifiants ou des détails exploitables. Contacter directement le référent projet via les canaux privés de l'équipe et inscrire, si nécessaire, un ticket Jira sans y joindre les données sensibles. **Aucune adresse de signalement externe n'est publiée sans consentement.**

## Bonnes pratiques de contribution

- Clés API dans `.env` local ignoré, jamais dans commit, README ou journal.
- Sources / notices médicales uniquement si leur licence et leur divulgation sont autorisées.
- Journaliser métadonnées minimisées (`trace_id`, `run_id`, version), jamais noms patients, prompts privés ou secrets.
- Données industrielles/simulées toujours étiquetées comme telles.
- Toute alerte issue de modèles est soumise à un humain habilité ; aucune action autonome sur machine.
- Après incident : contenir, documenter la version, supprimer les expositions selon procédures de la plateforme, réévaluer et approuver la correction via PR.

Le groupe doit déterminer ultérieurement une politique de divulgation et un contact sécurité adaptés avant déploiement réel.
