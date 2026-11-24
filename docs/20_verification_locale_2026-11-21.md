# Vérification locale RoboCare Sentinel — 21 novembre 2026

## Environnement et périmètre

Windows, Python 3.12.2, Node 22.13.0, SQLite Python ; branche
`feature/RCS-38-monitoring-quatre-vues`, base de travail initiale `0d8a815`.
Le dépôt a été ouvert dans l'éditeur Cursor. Aucun paquet tiers n'a été ajouté
pour RCS-38. Les autres modules ont été exécutés dans des worktrees séparés,
sans les fusionner au prototype ni à `main`.

## Application réellement testée

Serveur lancé avec `python -m tools.rcs38_demo_server --port 8000 --db .local/rcs38.sqlite3`.
Parcours dans Chrome à http://127.0.0.1:8000/ :

- Équipements : 4 appareils fictifs, disponibilité réelle ND.
- Données/anomalies : 4 observations fictives, 2 alertes candidates, 1 observation
  invalide ; vérité terrain et performances cliniques ND.
- Maintenance : tentative sans confirmation refusée ; ACT-DEMO-01 approuvée,
  ACT-DEMO-02 rejetée avec `signal_non_confirme`, après confirmation explicite.
  Les deux événements portent rôle `technicien-demo`, UUID et date UTC.
- Plateforme/Green AI : 2 runs fictifs ; filtre A puis B vérifié (un run par site).
  Coût illustratif respectivement 0,002 € et 0,007 €, sans dépense réelle.
  Énergie distante et p95 ND.
- Après arrêt et redémarrage du serveur sur la même base, rechargement du
  navigateur : approbation et rejet toujours visibles avec leurs traces.
  Lecture SQLite directe : 2 événements ; `PRAGMA integrity_check` → `ok`.

Les tableaux se font défiler dans la fenêtre Chrome de 882 × 672 ; ce contrôle
ne remplace pas un audit responsive multi-appareils ou d'accessibilité complet.
Le mode statique public a été observé en lecture seule ; son workflow sans API
n'a pas fait l'objet d'une nouvelle campagne complète de tests navigateur.

## Corrections et tests

- Le chargeur API applique désormais le validateur de fixtures existant
  (sites fictifs autorisés, champs patients/secrets interdits, énergie distante ND).
- GET/HEAD/POST refusent un Host non local, en complément du bind loopback et
  du contrôle d'origine. Ce garde-fou n'est pas une authentification.
- Les valeurs et unités sont échappées avant insertion HTML ; la navigation
  conserve ses boutons au changement de vue pour éviter de recréer le focus.
- Ajout d'exclusions Git pour caches Python et bases locales ; `.local/` était
  déjà exclu par son propre `.gitignore`.
- Workspace et tâches Cursor : serveur, tests Python, tests des rendus JS.

Commandes exécutées :

```bash
python -m unittest discover -s tests -v
python -m tools.rcs38_contract
node --check frontend/monitoring/app.js
node --test tests/test_rcs38_frontend.cjs
```

16 tests Python et 3 tests de rendu JS. Ces derniers exécutent les fonctions de
rendu dans Node avec un DOM minimal : ce ne sont pas des tests navigateur.
Les tests API ouvrent de vrais sockets locaux et des bases SQLite temporaires ;
ils incluent deux décisions concurrentes : une seule réussit, l'autre reçoit 409,
et un seul événement est conservé.

## Vérifications séparées

| Module | Référence initiale | Exécution et résultat |
|---|---|---|
| RCS-69 | `041e60a`, docs/RCS-69-preparer-cas-diffusion | 10 tests réussis ; audit : 10 cas proposés, 0 gelé ; baseline puis mini-DDPM NumPy entraîné avec seed 42 et 250 updates sur les seuls signaux artificiels existants. JSON conservé localement. Aucune validation biomédicale. |
| RCS-81 | `f6aa07c`, experiment/RCS-81-evaluation-tp04-tp05 | 6 tests initiaux réussis. Tests complémentaires reproduisant 5 échecs avant correction (espaces, versions, modèles V2), puis 10 tests réussis. Commande par défaut : BLOCKED/cases_not_frozen. Aucun appel LLM. |
| RCS-90 | `c19eb4e`, feature/RCS-90-suivi-couts-complets | 9 tests réussis ; calculateur lancé sur registres vierges : montants, heures et coût par succès null/ND. Aucun montant ni temps réel ajouté. |

## Reste à faire

Revue UX par Aminata, validation indicateurs par Omar et revue architecture/sécurité
par Ayoub ; aucun de ces accords n'est remplacé par l'exécution technique.
Choisir et autoriser les sources, faire approuver puis geler les cas RCS-69/81,
fixer les modèles et versions, réaliser les benchmarks réels avec preuves,
collecter coûts et heures documentés pour RCS-90.
Le rôle affiché est une simulation : authentification, RBAC et déploiement de
production ne sont pas implémentés. Aucun équipement ni patient connecté.

PR #8 et les PR associées restent soumises à revue ; aucune fusion ni modification
de protection de `main` n'a été effectuée.
