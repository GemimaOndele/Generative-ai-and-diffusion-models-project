# 📚 Manifeste de données — provenance, droits et qualité

**État : aucune source de télémétrie hospitalière réellement autorisée et validée pour le projet.** La famille pilote de dispositifs reste à choisir. Un jeu industriel ou artificiel doit être étiqueté **non médical**.

| Source/version | Objectif | Format / modalité | Licence et autorisation | Sensibilité | Hash/provenance | Splits indépendants | Limites |
|---|---|---|---|---|---|---|---|
| **À sélectionner** | Détection J1 / documents J2 | À confirmer | **À vérifier** | À vérifier | À renseigner après accès | Train/val/test gelé à définir | Industrialisation ≠ validation biomédicale |

**Sources candidates à examiner**, sans supposer l'autorisation ou la validité :
- UCI **AI4I** : données de maintenance industrielle tabulaire artificielle, pas des capteurs médicaux.
- **MIMII DUE** : anomalies acoustiques de machines industrielles, pas d'équipements biomédicaux.
- openFDA MAUDE / rappels : signalements, **pas** des séries temporelles de capteurs.
- AccessGUDID : métadonnées d'identification des dispositifs, **pas** un journal de pannes.
- Documentation technique autorisée : pour RAG, vérifier droits d'accès et licences.

**Ne jamais pousser** de données patient, fichiers non autorisés, clés, séries brutes privées ou données personnelles. Référencer une [dataset card](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/4) par version et un manifeste par expérience, avec unités et traitement des valeurs manquantes.

Lien [RCS-40 — contrat de données](https://gemimakerenondelepourou.atlassian.net/browse/RCS-40).
