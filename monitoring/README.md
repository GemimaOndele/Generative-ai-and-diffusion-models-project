# RoboCare Sentinel — aperçu public RCS-38

Cette page GitHub Pages montre uniquement les quatre vues de monitoring, les données
artificielles, les tableaux et les filtres. Aucun appel API ni validation de maintenance.

- Site vitrine : https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/
- Aperçu : https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/monitoring/
- Branche de développement : https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/8

Pour l'expérience complète EN LOCAL, récupérer la branche de la PR #8, puis :

```bash
python -m tools.rcs38_demo_server --port 8000 --db .local/rcs38.sqlite3
```

Ouvrir http://127.0.0.1:8000/ pour approuver/rejeter des alertes FICTIVES,
consulter le journal et constater la persistance SQLite.
Ne jamais exposer ce serveur local non authentifié sur Internet.
La page publique et le code local ne comportent ni patient ni équipement réel.
