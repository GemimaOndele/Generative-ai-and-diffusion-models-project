# RCS-88 — Matrice biais / robustesse

> Résultats et seuils ND : aucune conclusion d'absence de biais.

| ID | Système | Dimension | Sous-groupe/condition | Risque | Métrique | Résultat | Seuil | Test | Mitigation | Statut |
|---|---|---|---|---|---|---|---|---|---|---|
| B-001 | MC-baseline | type_appareil | ND | Faux négatifs sur une famille d'appareils | Rappel par sous-groupe autorisé | ND | ND | T01–T06 + regroupement par type d'appareil | Rééquilibrage ou revue humaine après décision explicite | Ouvert |
| B-002 | MC-diffusion-j1 | regime_signal | Bruit élevé / capteur dégradé | Reconstruction trompeuse | Erreur de reconstruction et delta de détection | ND | ND | Cas J1 gelés + cas réels autorisés | Filtrage qualité du signal, comparaison au baseline | Ouvert |
| B-003 | MC-mono-llm | format | Source absente / contradiction | Réponse non fondée ou faux refus | Taux d'abstention correcte et exactitude des citations | ND | ND | T07–T08 (TP04) | Abstention, citations, revue humaine | Ouvert |
| B-004 | MC-v2-multillm | format | Injection / données sensibles | Sortie non sûre ou fuite | Taux de refus correct et nombre d'appels | ND | ND | T09–T10 (TP04) | Séparation des instructions, RBAC, masquage, revue humaine | Ouvert |
| B-005 | Tous | site | Nouveau lot / firmware | Dérive temporelle | Delta de métriques vs baseline | ND | ND | Monitoring périodique et cas de non-régression | Alerte, réévaluation et rollback | Ouvert |
| B-006 | MC-mono-llm | langue | Langue non couverte ou ambiguë | Réponse non fondée ou faux refus | Taux d'abstention correcte par langue autorisée | ND | ND | T07–T08 avec variante de langue, si corpus autorisé | Abstention et revue humaine | Ouvert |

## Dimensions autorisées (si données autorisées)

| Dimension | Description |
|---|---|
| type_appareil | Type d'appareil (catégories autorisées par le manifeste) |
| site | Site ou lot (identifiant non sensible, si autorisé) |
| regime_signal | Régime du signal (bruit, plage, qualité) |
| langue | Langue des documents RAG |
| format | Format ou modalité d'entrée |
