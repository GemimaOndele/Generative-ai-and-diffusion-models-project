# Publication GitHub Pages — RoboCare Sentinel

**Préparation technique terminée sur PR #1 et sur la branche indépendante `gh-pages` ; la publication et l'adresse publiques restent à vérifier.** Le site cible est une **vitrine publique de recherche** : il ne constitue pas une plateforme biomédicale opérationnelle, ne collecte aucune donnée et n'a aucune connexion à un dispositif réel.

## Fichiers préparés
- `docs/index.html` : accueil du projet (mission, quatre vues, architecture, J1/TP04/TP05, équipe).
- `docs/landing.css` : mise en page responsive, styles holographiques/3D, animation légère, `prefers-reduced-motion`.
- `docs/landing.js` : onglets accessibles clavier, menu mobile, aucun appel distant ou état stocké.
- `docs/assets/robocare-hero-animated.svg` et `docs/assets/architecture.svg` : illustrations originales.
- `docs/.nojekyll` : publication de fichiers statiques sans transformation Jekyll.
- Tests CI : présence/validité des fichiers, contraintes de sécurité et absence de données de santé.

## Vérifier et configurer la publication — SANS attendre la PR #1
1. La branche **[`gh-pages`](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/tree/gh-pages)** existe déjà, avec `index.html`, CSS, JavaScript et SVG à la racine. Elle n'est pas protégée par la règle de `main` et n'a pas besoin de fusion de PR #1.
2. Ouvrir la page **Settings → Pages** du dépôt.
3. Dans **Build and deployment**, choisir **Source : Deploy from a branch**.
4. Choisir **Branch : gh-pages** et **Folder : /(root)** (source : `gh-pages / (root)`), puis **Save**.
5. Attendre l'état de déploiement GitHub et vérifier l'URL renvoyée par la plateforme.
6. Après vérification, remplir la section **About → Website** avec l'URL réellement publiée.

**Adresse attendue (NON VÉRIFIÉE comme accessible)** :
`https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/`.

> Pour l'instant, la connexion GitHub de ChatGPT permet de créer/modifier des fichiers, des branches et des PR, mais **ne fournit pas de modification des paramètres administratifs de Pages**. La création de la branche a fait apparaître `has_pages=true` dans les métadonnées GitHub, sans que la source exacte ou la mise en ligne puisse être confirmée depuis le connecteur.

## Vérifier localement l'aperçu sans publier
Depuis la **branche `gh-pages`** :
```bash
python -m http.server 8000
```
Ouvrir `http://localhost:8000/` dans Chrome ou Cursor. La page doit montrer les visuels SVG et permettre de changer les onglets J1/J2/TP05 et le menu mobile.

## Conditions de publication
- Bannière fictive : appareil biomédical symbolique non représentatif d'une marque/machine réelle.
- Pas de formulaire, cookies de suivi, collecte de données personnelles, secrets ni appels LLM.
- Texte du site vérifiable, résultats scientifiques absents explicitement signalés.
- Accord collectif sur publication et visuels, revue d'un membre autre que l'auteur.
- Si des informations confidentielles sont ajoutées ultérieurement : bloquer la publication, revoir les droits et procéder à la revue sécurité.

Documentation : [GitHub Pages — Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Clarification à la suite de la revue d'Ayoub du 23/11/2026

**Source de publication souhaitée :** `gh-pages / (root)`, à confirmer dans les paramètres du dépôt. Le dossier `docs/` présent sur la PR #1 contient une **copie de préparation historique** du site et ne doit **pas** devenir une seconde source de déploiement. Ne pas choisir `main /docs` comme source Pages. Lors d'une modification du site, mettre à jour **la branche publiée** `gh-pages` via sa propre revue ; ne pas continuer deux versions divergentes.

Les SVG `docs/assets/robocare-hero-animated.svg` et `docs/assets/architecture.svg` de la PR #1 restent utiles à la présentation de `README.md` sur `main`, et leur présence n'active pas une seconde publication. La question du retrait ou de l'archivage des trois fichiers `docs/index.html`, `docs/landing.css`, `docs/landing.js` de la branche de préparation doit être tranchée avec Ayoub en vérifiant d'abord les tests CI qui les référencent ; ne les supprimer ni les déplacer silencieusement.

**État de revue GitHub :** une recommandation de squash dans un commentaire n'est pas une approbation formelle. Voir la PR #1 et ses contrôles.
