# RCS-88 — Protocole biais et refus

Refus par défaut : sans preuve par sous-groupe autorisé, aucune conclusion de biais ou d'absence de biais.

## Règles

- Aucun attribut sensible n'est inféré, demandé ou stocké dans les livrables.
- Un sous-groupe absent du manifeste ou non autorisé est refusé : « évaluation non disponible ».
- Une métrique sans jeu de données identifié, provenance et taille d'échantillon reste ND.
- Un résultat par sous-groupe n'est publié qu'après revue humaine.
- Le monitoring signale une dérive ; il ne déclenche aucune action autonome sur un appareil.

## Étapes

1. Définir les dimensions autorisées et pertinentes.
2. Geler un jeu de cas autorisé et documenter la provenance.
3. Mesurer la performance globale et par sous-groupe autorisé uniquement.
4. Analyser faux positifs, faux négatifs, faux refus et cas sensibles.
5. Documenter limites, incertitude et interdiction d'usage hors périmètre.
6. Décider GO / NO-GO avec relecteur humain et tracer la décision.

**Sortie par défaut :** évaluation non disponible  
**Escalade :** Revue humaine obligatoire ; pas de décision clinique ni d'action autonome.
