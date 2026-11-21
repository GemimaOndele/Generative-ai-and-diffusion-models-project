# Publication GitHub Pages — RoboCare Sentinel

**Préparation technique terminée sur PR #1 ; publication GitHub Pages NON activée.** Le site cible est une **vitrine publique de recherche** : il ne constitue pas une plateforme biomédicale opérationnelle, ne collecte aucune donnée et n'a aucune connexion à un dispositif réel.

## Fichiers préparés
- `docs/index.html` : accueil du projet (mission, quatre vues, architecture, J1/TP04/TP05, équipe).
- `docs/landing.css` : mise en page responsive, styles holographiques/3D, animation légère, `prefers-reduced-motion`.
- `docs/landing.js` : onglets accessibles clavier, menu mobile, aucun appel distant ou état stocké.
- `docs/assets/robocare-hero-animated.svg` et `docs/assets/architecture.svg` : illustrations originales.
- `docs/.nojekyll` : publication de fichiers statiques sans transformation Jekyll.
- Tests CI : présence/validité des fichiers, contraintes de sécurité et absence de données de santé.

## Pour activer la publication — seulement après approbation et fusion de PR #1
1. Vérifier que la PR #1 a reçu les approbations exigées, que les contrôles GitHub Actions sont au vert, puis fusionner.
2. Ouvrir la page **Settings → Pages** du dépôt.
3. Dans **Build and deployment**, choisir **Source : Deploy from a branch**.
4. Choisir **Branch : main** et **Folder : /docs**, puis **Save**.
5. Attendre l'état de déploiement GitHub et vérifier l'URL renvoyée par la plateforme.
6. Après vérification, remplir la section **About → Website** avec l'URL réellement publiée.

**URL qui serait normalement utilisée pour un site de projet sur GitHub Pages, mais NON VÉRIFIÉE comme active** :
`https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/`.

> Pour l'instant, la connexion GitHub de ChatGPT permet de créer/modifier des fichiers, des branches et des PR, mais **ne fournit pas de modification des paramètres administratifs de Pages**. Le réglage n'a donc pas été modifié.

## Vérifier localement l'aperçu sans publier
Depuis la **branche PR #1** :
```bash
python -m http.server 8000 --directory docs
```
Ouvrir `http://localhost:8000/` dans Chrome ou Cursor. La page doit montrer les visuels SVG et permettre de changer les onglets J1/J2/TP05 et le menu mobile.

## Conditions de publication
- Bannière fictive : appareil biomédical symbolique non représentatif d'une marque/machine réelle.
- Pas de formulaire, cookies de suivi, collecte de données personnelles, secrets ni appels LLM.
- Texte du site vérifiable, résultats scientifiques absents explicitement signalés.
- Accord collectif sur publication et visuels, revue d'un membre autre que l'auteur.
- Si des informations confidentielles sont ajoutées ultérieurement : bloquer la publication, revoir les droits et procéder à la revue sécurité.

Documentation : [GitHub Pages — Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
