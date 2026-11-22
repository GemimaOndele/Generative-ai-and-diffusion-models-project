# RoboCare Sentinel — revue transverse et cadrage multi-équipements (22/11/2026)

> Note de coordination proposée par Gémima. **Document de revue, non une décision validée**, fondée sur Jira RCS et des branches GitHub consultées le 22/11/2026. Ne modifie aucun livrable existant et ne démarre pas le Sprint.

## 1. Périmètre scientifique à distinguer

**Périmètre général** : maintenance intelligente, aide à la décision et génération de données / contenus multimodaux pour plusieurs familles d'équipements médicaux. Les modalités *candidates* incluent capteurs et signaux temporels, journaux techniques, rapports d'intervention, documentations textuelles et éventuellement images, uniquement avec des sources légales et des objectifs de génération définis. Un modèle de diffusion entraîné sur un signal tabulaire industriel **ne prouve pas** la génération multimodale d'équipements médicaux.

**Prototypes ciblés** : un sous-ensemble limité d'équipements pour les expériences contrôlées. Les dispositifs critiques (ex. ventilateurs/respirateurs, pompes à perfusion) sont des **candidats de scénario documentaire LLM**, pas un choix voté ni une autorisation de déploiement clinique. Toute suggestion d'intervention garde une validation humaine, des sources vérifiables et un refus en l'absence d'information fiable.

**Décisions distinctes** à soumettre au groupe :
1. Familles couvertes dans la **taxonomie** et les interfaces (ouverte, extensible) ;
2. Famille(s) réellement **évaluées par diffusion** selon disponibilité des données et licences ;
3. Dispositif(s) de **démonstration documentaire Multi-LLM** (sensibilité, corpus, procédures, interdictions, critères de refus) ;
4. Source et modalités des **données réelles ou substituts**, niveau de preuve et limites de généralisation.

Le tableau de vote Excel est lié dans [RCS-19](https://gemimakerenondelepourou.atlassian.net/browse/RCS-19). Le lire et recueillir les cinq réponses avant toute décision officielle ; **son contenu n'a pas été audité ici**.

## 2. Audit des contributions complémentaires

| Domaine | Preuve identifiée | Statut / limite |
|---|---|---|
| Fonctionnel — Aminata | RCS-12 terminé ; RCS-20 BPMN AS IS 7 étapes + Excel ; RCS-21 personas + Excel ; RCS-23 fiche openFDA ; RCS-19 tableau de vote | RCS-19/20/21/23 en revue ; chiffres métier non mesurés ; approbations humaines manquantes |
| Données — Omar | branches `data/RCS-40-dictionnaire-contrat-donnees`, `docs/RCS-24-audit-accessgudid`, `docs/RCS-25-audit-ai4i-mimii-due` | Contrats et sources à relire ; AI4I est **industriel non médical** |
| Pipeline — Omar | `feature/RCS-49-ingestion-csv-validations` (import CSV, quarantaine, idempotence SHA-256) ; `feature/RCS-50-stockage-poc` (SQLite) ; `feature/RCS-52-vue-mesures-anomalies` (Streamlit) | Branches non fusionnées ; API openFDA non intégrée au pipeline CSV ; attention, AI4I ne contient pas de chronologie médicale |
| Diffusion — Omar | `experiment/RCS-71-baseline-vs-diffusion-memes-cas` : DDPM tabulaire, comparaison z-score / Isolation Forest, 3 seeds et résultats sur substitut AI4I | Diffusion meilleure en PR-AUC sur variables brutes, mais règle simple meilleure sur variables physiques ; aucun résultat sur machine médicale |
| Multi-LLM — Omar | `experiment/RCS-77-comparer-mono-routing-cascade` : deux petits LLM locaux, 10 cas, routing, cascade et garde-fous ; `docs/RCS-82-finops-cout-par-tache-reussie` : FinOps/CodeCarbon | Benchmark documenté sur corpus de démonstration ; échecs de fidélité de citation, contradiction de versions et latence ; évaluation humaine et revue sécurité encore nécessaires |
| GitHub — équipe | 9 PR ouvertes au 22/11, créées sous le compte `GemimaOndele` ; contributions d'Omar principalement sur branches dédiées | **Branch ≠ PR ≠ merge**. La branche `main` ne comprend pas les développements ci-dessus ; ne pas les déclarer intégrés |
| Elias / Ayoub | Plusieurs branches réservées mais encore identiques à `main` lors du contrôle | Pas de livraison autonome prouvée sur ces branches ; ne pas interpréter l'absence de commit comme absence de travail hors GitHub |

## 3. Intégration cible — éviter deux plateformes concurrentes

- **Point de convergence** : RCS-38 (interface 4 volets + serveur de démonstration local) et RCS-52 (vue Streamlit source/mesures/anomalies) doivent partager **un modèle de lecture**, une provenance et des statuts plutôt que remplacer l'un par l'autre.
- **Inventaire multi-équipements** : prévoir `equipment_family`, `equipment_type`, `equipment_id`, `manufacturer`, `site`, `criticality`, `data_modality` (tous facultatifs quand la source ne les fournit pas), ainsi qu'une indication explicite `real_medical / proxy_industrial / synthetic_demo`. Ces noms sont une **proposition de contrat**, pas une migration SQL.
- **Chaîne cible** : source autorisée → manifest/licence → ingestion + validation → stockage/provenance → baseline/diffusion → score/alerte → validation humaine + audit → interface.
- **Contrats à concilier** : `src/rcs/db.py` et `src/rcs/ingestion.py` apparaissent sur plusieurs branches Omar ; RCS-38 dispose d'une SQLite locale dédiée aux alertes fictives. Définir la frontière de propriété des modules avant le premier merge.
- **API** : versionner les schémas des équipements, observations, scores, anomalies, décisions, preuves de sources et statuts de provenance. Aucun appel direct à un équipement médical ; démo locale séparée de la version GitHub Pages statique.
- **Deux axes IA** : J1 diffusion = métriques sur cas gelés et données licenciées ; J2 Multi-LLM = corpus documentaire restreint, modèles A/B réellement distincts, citations vérifiées, refus, tests de stress et coût/CO₂e par tâche réussie.

## 4. Revues et critères de réception proposés

1. **RCS-19 — groupe/Aminata** : renseigner le vote Excel, puis voter séparément *largeur du catalogue* et *périmètre expérimental* ; ne pas assimiler respirateur de réanimation, pompe à perfusion et capteur industriel.
2. **RCS-23 — Gémima + Aminata** : valider openFDA comme signalement/recall + source de contexte documentaire ; ne jamais l'utiliser comme série capteur ni taux de panne. Exclure les identifiants personnels et contrôler licence/actualisation.
3. **RCS-38 ↔ RCS-49/50/52 — Gémima, Omar, Ayoub, Aminata** : comparer champs, états, unités, routes, jeux de test et niveaux de preuve ; choisir **une** expérience utilisateur et une interface d'intégration ; garder les démos indépendantes jusqu'aux tests.
4. **RCS-69 ↔ RCS-71 — Gémima, Omar, Elias** : expliquer le rapport entre mini-DDPM sur signaux artificiels et expérience tabulaire AI4I, éviter toute revendication de validité médicale ; geler les cas et hypothèses à l'avance.
5. **RCS-81 ↔ RCS-77/82 — Gémima, Omar, Elias, Aminata** : auditer mêmes cas, versions, jugements, latence, coût et énergie ; investiguer l'échec T07/T08 (réponses sans fondement / source obsolète), tester contrôle de fidélité et abstention.
6. **GitHub — Ayoub + équipe** : transformer les branches réalisées en PRs relisibles avec diff, CI, reviewer, preuve d'exécution et critères Jira. **Ne pas tout fusionner directement** : les branches de pipeline partagent du code ; arbitrer l'ordre RCS-40/41/42 → RCS-49 → RCS-50 → RCS-52.
7. **Drive / sources — équipe** : inventaire des documents Excel, données autorisées, versions, liens, propriétaires, licences, données sensibles et correspondance vers Jira/GitHub. Pas de copie publique des sources sous contrôle d'accès sans autorisation.

## 5. Prochaines actions de Gémima

- Effectuer sa relecture des tickets RCS-19/RCS-23 et contribuer au vote de la famille cible.
- Valider le contrat d'intégration RCS-38 / RCS-52 sans écraser la vue d'Omar ; prévoir un prototype unifié **après** consensus de schéma.
- Consolider son protocole RCS-81 avec résultats documentés RCS-77/82 (statuts mesuré/calculé/estimé/ND, pas d'invention de tests).
- Compléter RCS-17 : capacités réelles des cinq membres, validation des échéances déjà proposées, revue collective des PR avant début du Sprint.
- Préparer une présentation fidèle du niveau de maturité : expérimentation sur **substituts**, démonstration logicielle locale, sources biomédicales documentaires, aucune évaluation clinique.

## 6. Conditions avant publication ou utilisation

Aucune donnée patient ; aucune clé d'API ni fichier sensible dans le dépôt ; aucune automatisation de décision clinique ; aucune assertion de performance biomédicale à partir d'AI4I ou de signaux synthétiques. Les feuilles du Drive et pièces jointes Jira non effectivement ouvertes ne sont **pas considérées comme auditées**. Ce document sollicite une **revue par l'équipe** ; il ne remplace ni le cahier des charges ni le vote de RCS-19.
