# RCS-38 — Quatre volets de monitoring : premier prototype web exécutable

**Référente : Gémima. Binôme : Aminata. Relais : Ayoub. Relecteur : Omar.**  
**Statut : prototype navigable, non validé fonctionnellement, sans données réelles ni connexion au SI biomédical.**

## Prototype à ouvrir dans Cursor
Après récupération de la branche `feature/RCS-38-monitoring-main-integration-20261123` :

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Ouvrir `http://localhost:8000/frontend/monitoring/`. Cliquer les **quatre volets**, puis filtrer les sites **A/B**. Le fichier `frontend/monitoring/demo.json` contient uniquement des fixtures fictives et l'UI affiche en permanence le bandeau « démonstration ». Aucun framework nécessaire.

## Spécification de chacun des quatre volets
| Vue | Contenu cible | Prototype effectivement livré | Critères métier restant à valider |
|---|---|---|---|
| Parc équipements | identifiant, site, famille, état, disponibilité | Inventaire fictif filtrable, état déclaré | Choisir famille pilote, catalogue autorisé, droits, seuil disponibilité |
| Données & anomalies | qualité capteurs, anomalies, FP/FN, dérive | Valeurs fictives, qualité, alertes candidates ; métriques scientifiques ND | Sources, étiquettes, seuils et gestion anomalies de données (RCS-69) |
| Maintenance & interventions | alertes revues, intervention, validation technicien, historique | Tableau des interventions fictives et étapes du workflow | RBAC, trace d'approbation, formulaires réels et aucun ordre machine |
| Plateforme & Green AI | p95, coût par succès, versions modèle/données, énergie local/API, incidents | Exécutions fictives, versions, coût simulé et énergie distante ND | Instrumentation RCS-81/82/83/87/89/90, budget, couverture et provenance |

**Les chiffres du prototype sont fictifs et ne constituent pas des KPI réels.** La qualité et la latence p95 restent `ND` faute de tests gelés ; la CO₂e des API distantes reste `ND`. CodeCarbon local ne mesure pas le fournisseur distant.

## Tests
```bash
python -m unittest discover -s tests -p 'test_rcs38_monitoring.py' -v
python -m tools.rcs38_contract
node --check frontend/monitoring/app.js
```

Le contrôle automatique vérifie le nombre des vues, la cohérence des fixtures, la politique de `null` pour l'énergie distante, l'absence de clés/patients dans les champs, et la syntaxe JS. **Il ne remplace pas une revue UX ou un test de sécurité applicative réel.**

## Prochaines étapes avec les membres
- **Aminata (binôme)** : tester les quatre parcours, définir le lexique de métier, vérifier l'absence de décisions automatiques.
- **Omar (relecteur)** : contrôler KPI, champs, statuts et futures sources/qualité de données.
- **Ayoub (relais technique)** : intégrer le prototype dans l'architecture web sur le nouveau socle main après la fusion de la PR #1, préparer tests d'API et observabilité.
- **Gémima** : mettre en correspondance les écrans du cahier des charges V1.3, l'évolution RCS-86 et les décisions du groupe.

RCS-38 phase initialement indicative S2 : ce premier prototype ne signifie pas que l'intégration applicative et la validation d'écrans sont terminées. PR distincte ; ne pas fusionner avant la revue humaine.


## Itération 2 — API locale, SQLite et validation humaine simulée

**Ce composant est un POC pédagogique local, sans authentification réelle ni usage biomédical.**

Pour lancer la version interactive depuis la branche RCS-38 :

    python -m tools.rcs38_demo_server --port 8000 --db .local/rcs38.sqlite3

Ouvrir ensuite http://127.0.0.1:8000/ . Le serveur écoute uniquement sur 127.0.0.1.

Le mode statique existant reste en lecture seule :

    python -m http.server 8000 --bind 127.0.0.1

Puis http://127.0.0.1:8000/frontend/monitoring/ .

**Contrat HTTP fictif :** GET /api/v1/demo/health ; GET /api/v1/demo/overview ; POST /api/v1/demo/actions/{id}/decision. La requête POST est un objet JSON avec decision (approved/rejected), reason_code (contrôle confirmé, signal non confirmé ou qualité insuffisante en code), acknowledge_simulation=true.

Le serveur vérifie la confirmation, les motifs codifiés, l'origine HTTP, le Content-Type et l'état en attente. Il refuse une seconde décision (409), sauvegarde l'état dans SQLite et génère une trace UUID, horodatage UTC et rôle explicite technicien-demo. La carte Maintenance expose le journal, notamment le rôle simulé et le motif codifié. Une justification libre n'est pas ajoutée afin d'éviter toute saisie de données personnelles ; les motifs complémentaires doivent être définis collectivement. Aucun nom de patient, aucune commande machine, aucune connexion hospitalière.

Le mode local est **mono-utilisateur, sans mécanisme d'identification vérifié** : ne jamais publier cette API sur GitHub Pages, sur un réseau public ou un serveur de production. Seule l'interface publique statique peut être hébergée séparément.

**Tests** : python -m unittest discover -s tests -p 'test_rcs38_api.py' -v ; python -m unittest discover -s tests -p 'test_rcs38_monitoring.py' -v ; node --check frontend/monitoring/app.js .

**Relectures restantes :** Aminata (compréhension et ergonomie des décisions), Omar (KPI/statuts), Ayoub (contrat API, sécurité et authentification future). Les écrans et indicateurs sont encore en attente de validation métier.

## Revue manuelle UX à réaliser sur le dernier commit

- [ ] Parc : naviguer, filtrer A/B, vérifier le bandeau fictif.
- [ ] Données : vérifier la qualité et les alertes candidates.
- [ ] Maintenance : tester refus sans confirmation, approbation et rejet simulés ; vérifier motif, rôle, date et persistance après redémarrage.
- [ ] Plateforme : distinguer données simulées, valeurs ND et mesures réelles absentes.
- [ ] Consigner le commit, l'environnement, les résultats et les réserves du relecteur. Cette checklist ne vaut pas preuve d'exécution.
