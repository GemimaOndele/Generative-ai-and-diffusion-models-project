# Cartographie des risques, enjeux et biais — RoboCare Sentinel

**Gabarit de travail : aucune probabilité ni gravité réelle n'a été approuvée.** Source : TP05 ECE du 20/11/2026 et rappel oral rapporté par le groupe. RCS-18 (registre existant), RCS-66, RCS-84 et RCS-88.

## Registre vivant
Le registre canonique RCS-18 (#35) recense ID, composant et version, danger/événement déclencheur, parties touchées, source du risque, probabilité (échelle à convenir), gravité, matrice d'exposition initiale, contrôle, responsable, binôme, relecteur, test, preuve, exposition résiduelle, statut, échéance de revue, action en cas de dépassement.

**Méthode proposée :**
- Coter probabilité et impact de 1 à 5 selon la proposition RCS-18 (#35), **uniquement après consensus et critères écrits**.
- Positionner les risques dans une matrice 5 × 5, prioriser les risques élevés, avec validation séparée des critères de refus pour risques critiques.
- Revoir aux portes de décision, lors d'un changement de modèle/dataset/corpus, d'une anomalie, et à chaque Sprint.
- Enregistrer risques émergents et incidents, pas seulement une matrice figée au cadrage.

## Risques candidats à évaluer (hypothèses, pas des incidents observés)
| Risque | Conséquence potentielle | Indicateur/test candidat | Réduction |
|---|---|---|---|
| Données industrielles non représentatives du médical | fausse assurance de performance | sous-groupes appareils/sites disponibles, provenance, écart de domaine | étiquetage strict « non médical », validation experte |
| Faux négatifs / faux positifs de détection | alerte manquée ou surcharge technicien | précision/rappel, matrice de confusion, délai de traitement | seuil, revue humaine, qualification d'incident |
| Réponses RAG non fondées | erreur d'interprétation documentaire | test T07 source absente, citations exactes, abstention | garde-fous, source et validation |
| Injection indirecte | fuite ou action non autorisée | test T09 source malveillante | instructions séparées, RBAC, filtrage |
| Données patients / rétention des traces | divulgation d'informations sensibles | test T10, audit logs et droits | minimisation, pas de données patients, suppression contrôlée |
| Coût et boucles d'agents | dépassement budgétaire | appels par trace, retries, p95, coût/usage | budgets/quotas, fallback sous autorisation |
| Dérive et changement de version | dégradation non détectée | changement de distribution et tests de non-régression | registre de versions, réévaluation/rollback |
| Énergie non observable des API | communication environnementale trompeuse | statut mesure/estimation/ND | frontière séparée, transparence CodeCarbon |

## Biais des modèles et jeux de données
La fiche de données (dataset card) et la fiche de modèle (model card) doivent préciser : provenance, périodes, modalités/sous-groupes **disponibles légalement**, taux de manquants, sélection/étiquetage, cas critiques, biais de couverture, faux positifs/négatifs, limites du transfert et zones de non-validité. Si un groupe n'est pas présent ou pas autorisé : **évaluation non disponible**, jamais « aucun biais ».

**Preuves minimales :** cas gelés, métriques par groupe lorsque possible, matrices d'erreurs et d'abstention, décision de seuil, relecteur et version. Le monitoring ne déclenche aucune action autonome sur les machines.

## Pilotage des risques
RCS-18 : propriétaire de la matrice et revue ; RCS-88 : biais et model cards ; RCS-89 : signaux d'alerte et incidents ; RCS-90 : risque financier et disponibilité humaine ; RCS-84 : test éthique TP05. L'audit n'est pas une certification RGPD/AI Act.

Le fichier `governance/templates/risk_register_template.csv` est un ancien gabarit de collecte, pas un second registre opérationnel. Les cotations #35 restent proposées jusqu'à ratification.
