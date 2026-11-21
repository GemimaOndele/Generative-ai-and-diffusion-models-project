# RCS-24 — Fiche source AccessGUDID (NLM / FDA)

Pages officielles consultées le **2026-11-20** (citations courtes ; vérifier toute mise à jour avant usage). Pilote : Omar · binôme : Aminata · relecteur : Ayoub.

| Champ | Constat |
|---|---|
| Nature | portail de la *Global Unique Device Identification Database* (GUDID), base administrée par la **FDA** dans le cadre du système UDI ; portail créé par la **NLM** (NIH) avec la FDA — https://accessgudid.nlm.nih.gov/ |
| Contenu | **identification des dispositifs uniquement** : Device Identifier (DI) ; les identifiants de production (lot, série, péremption) ne sont pas stockés, seule leur présence sur l'étiquette est indiquée. Mise à jour chaque jour ouvré. **Aucune donnée patient.** |
| Champs principaux (exemple API Device Lookup v3) | `identifiers.deviceId`, `brandName`, `versionModelNumber`, `catalogNumber`, `companyName`, `deviceDescription`, `deviceCount`, statut de publication et version, `gmdnTerms` (code, nom et définition GMDN, implantable), `productCodes` (code FDA, classe, panel), `MRISafetyStatus`, `sterilization`, `environmentalConditions`, indicateurs `singleUse`, `rx`/`otc`, `lotBatch`, `serialNumber`… |
| API | v3 `https://accessgudid.nlm.nih.gov/api/v3/` : **Device Lookup** (`/devices/lookup.json?di=…` ou `udi=` ou `record_key=`, JSON/XML), Device History, Device SNOMED, Parse UDI, Implantable List (ces quatre derniers non détaillés ici). v1 dépréciée. Aucun quota publié sur les pages lues → limiter le débit, mettre en cache. |
| Téléchargements | release complète mensuelle (2026-11-02 : 5 258 157 DI, 524 Mo, XML FDA, MD5 fourni) ; mises à jour quotidiennes/hebdo/mensuelles ; fichiers **délimités par pipe** pour import relationnel. |
| Conditions | conditions d'utilisation NLM : mention d'attribution NLM obligatoire, pas d'usage du nom/logo NLM. **GMDN sous licence de la GMDN Agency** : extraction pour services commerciaux ou entraînement d'IA soumise à licence. Données D&B (DUNS) : extraction automatisée interdite. Pas de licence ouverte explicite (type CC). |
| Historique maintenance / pannes | **absent**. Les rappels et la déclaration d'incidents sont des liens externes (openFDA/MedWatch), pas des champs GUDID. |

**Utilité métier pour RoboCare** : référentiel pour **identifier et catégoriser** l'équipement (`equipement.modele`,
`fabricant`, `classe`, catégorie GMDN, statut IRM) et faire la jointure avec les rappels/incidents openFDA par code
produit. **Pas** de télémétrie, de taux de panne ni d'historique de maintenance : inutilisable pour entraîner J1.
**Décision proposée** : usage optionnel en enrichissement (lookup ponctuel par DI d'un équipement fictif/de démo),
sans stocker les champs GMDN au-delà du strict nécessaire et avec la mention NLM. Pas d'ingestion de la release
complète (524 Mo, hors besoin du POC).
