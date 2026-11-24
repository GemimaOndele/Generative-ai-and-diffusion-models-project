# 🖥️ Interface web — RoboCare Sentinel

**État : premier prototype démonstratif disponible en PR, pas encore intégré dans `main`.**

Le [prototype RCS-38 — PR #8](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/8) contient une interface **HTML/CSS/JavaScript** avec quatre vues :
1. 🏥 Parc des équipements ;
2. 📈 Données et anomalies ;
3. 🧰 Maintenance et interventions ;
4. 🌱 Plateforme / Green AI.

Un filtre de site et les tableaux fonctionnent sur des **données inventées** (`frontend/monitoring/demo.json` de la PR #8). Aucun équipement réel, dossier patient ou LLM distant n'est connecté.

### Lancer localement après récupération de la branche RCS-38

```bash
python -m http.server 8000
```

Ouvrir `http://localhost:8000/frontend/monitoring/` dans Cursor/Chrome.

**Travail restant** : revue fonctionnelle d'Aminata, vérification des KPI par Omar, intégration API/DB par Ayoub selon architecture validée, contrôles d'accès et tests end-to-end. Les chiffres fictifs ne sont pas des indicateurs mesurés. [RCS-38](https://gemimakerenondelepourou.atlassian.net/browse/RCS-38) · [RCS-86](https://gemimakerenondelepourou.atlassian.net/browse/RCS-86).

Voir [le README général](../README.md) pour CM03, TP04, TP05 et le statut réel des PR.
