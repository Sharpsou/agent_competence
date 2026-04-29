# Notes projet

## Objectif

Construire un backend FastAPI clair, minimal, testable et pret a etre connecte a un futur front web.

Premier usage vise : interroger des sources d'offres d'emploi selon des filtres fournis avant l'appel, puis retourner des offres normalisees.

## Principes

- Commencer simple : `app/main.py` suffit tant que le besoin reste petit.
- Ajouter des dossiers seulement quand le code le justifie.
- Garder les conventions projet dans `.agents/skills/`, installees depuis `skills.sh`.
- Tests rapides pour chaque comportement public.
- Reprendre les apprentissages du projet local `D:\prog\actu_emploi` sans importer toute sa complexite.

## Jalon courant

Creer un backend d'interrogation d'offres d'emploi.

Entrees attendues avant l'appel :

- mots-cles ou intitules cibles
- localisation
- rayon de recherche si la source le permet
- source cible ou liste de sources
- nombre maximal d'offres
- filtres utiles : teletravail, type de contrat, date de publication, mots exclus

Sortie attendue :

- liste d'offres normalisees
- source et identifiant source
- titre, entreprise, localisation, contrat, mode de travail
- URL de detail quand disponible
- payload brut optionnel pour audit ou debug

## Prochaines etapes proposees

- Definir le contrat de requete `POST /jobs/search`.
- Creer un modele commun d'offre normalisee.
- Ajouter un premier connecteur inspire de `actu_emploi` : France Travail en priorite.
- Ajouter un cache local et une limite de requetes pour eviter les appels inutiles.
- Ajouter un connecteur Jooble ou web public ensuite, seulement si le premier flux est stable.
