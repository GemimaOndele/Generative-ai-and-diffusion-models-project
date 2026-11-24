# Coût complet, effort humain et temps de projet — RoboCare Sentinel

**Statut : modèle de prévision et de collecte, aucun montant du projet n'est déclaré mesuré.** RCS-90, RCS-65, RCS-82 et RCS-86. Le coût doit être examiné **dès le cadrage**, révisé au fil des itérations, pas seulement dans le rapport final.

## Quatre dimensions sans double comptage
1. **Argent déboursé** : API (tokens en/sortie, appels, retries, crédits), stockage/hébergement, GPU/cloud, licences, sauvegarde, services et énergie *si réellement facturée au projet*.
2. **Temps** : heures estimées puis réalisées par ticket et rôle (préparation de données, recherche, tests, recettage, documentation, maintenance, coordination) ; distinct des délais calendaires.
3. **Infrastructure** : machine, capacité, ressources réservées, environnements, logs, index RAG, utilisation réelle, amortissement hypothétique si argumenté.
4. **Coût humain** : effort des 5 étudiants, temps de revue par pairs et intervention/supervision d'un professionnel biomédical **si autorisé et observé** ; valorisation horaire **hypothétique et séparée** des dépenses réelles.

**Éviter les doubles comptes :** ne pas ajouter le coût serveur dans un prix API qui l'inclut déjà ; ne pas additionner heures de bénévolat et dépense de trésorerie sans afficher la convention de valorisation.

## Unités, formule et preuve
- `EUR_reels = somme dépenses effectivement facturées` (ou ND sans factures).
- `heures_reelles = somme heures déclarées`, statut « auto-déclaré », et non facturation.
- `EUR_equivalent_humain = heures × taux hypothétique` seulement dans les scénarios qui le nécessitent.
- `coût_total_par_succès = (coûts variables + coûts fixes alloués)/succès`, uniquement pour `succès > 0`; sinon **ND**.
- Comparer mono-A, mono-B et V2 sur **le même jeu gelé** et mêmes critères métier, puis comparer p95, sécurité et biais.
- Toute projection mensuelle doit distinguer coûts fixes et hypothèses de charge (3 scénarios pessimiste, central, optimiste).

`governance/cost_register.csv` est un **journal vide** à alimenter par événements datés et sourcés : type de coût, unité, quantité estimée/réelle, valeur, devise, fournisseur, modèle/version, source tarif, date, ticket, run, frontière, statut, reviewer.

## Surveillance continue
À chaque Sprint : budget prévu vs dépensé, effort prévu vs consommé, blocages, coût unitaire par succès s'il est calculable, dépassement des quotas et changement de tarification/version. L'interface pourra afficher ces indicateurs selon les droits ; aucune estimation ne doit être présentée comme une facture.

**Décision :** si coûts élevés ou données manquantes, évaluer alternatives techniques et dégradation de qualité/latence/risque avant de déclarer un gain FinOps.