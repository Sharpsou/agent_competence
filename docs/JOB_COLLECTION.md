# Collecte des offres d'emploi

Ce projet va interroger des sources d'offres d'emploi a partir de filtres fournis par l'utilisateur ou le futur front.

## Reference locale

Le projet `D:\prog\actu_emploi` contient deja une exploration utile :

- `src/python/actu_emploi_pipeline/sources/france_travail.py`
- `src/python/actu_emploi_pipeline/sources/jooble.py`
- `src/python/actu_emploi_pipeline/sources/public_web.py`
- `src/python/actu_emploi_pipeline/models.py`
- `src/python/actu_emploi_pipeline/normalize.py`
- `tests/python/test_france_travail_preferences.py`

On reprend les idees, pas toute l'architecture.

## Sources initiales

### France Travail

Approche observee dans `actu_emploi` :

- recherche via URL publique `https://candidat.francetravail.fr/offres/recherche`
- parametres utiles : `motsCles`, `lieux`, `rayon`, `tri`
- extraction de liens de detail depuis la page de resultats
- extraction du detail via JSON-LD `JobPosting` quand disponible
- codes de communes deja utiles :
  - Nantes : `44109`
  - Saint-Nazaire : `44184`

### Jooble

Approche observee :

- recherche web publique par role et localisation slugifies
- extraction de detail via JSON-LD `JobPosting`
- source a activer apres stabilisation du premier connecteur

## Filtres d'appel

Le futur endpoint devra accepter :

- `keywords`: liste de mots-cles ou roles
- `location`: texte utilisateur
- `location_code`: code source optionnel si connu
- `radius_km`: rayon optionnel
- `sources`: liste de sources a interroger
- `max_results`: limite globale ou par source
- `remote_mode`: `remote`, `hybrid`, `onsite` ou `any`
- `contract_type`: optionnel
- `published_since`: optionnel
- `excluded_keywords`: liste optionnelle

## Modele de sortie normalise

Champs minimaux :

- `source`
- `source_job_id`
- `title`
- `company_name`
- `location_text`
- `remote_mode`
- `contract_type`
- `description_text`
- `published_at`
- `detail_url`
- `raw_payload`

## Contraintes techniques

- Ne pas appeler les sources en boucle sans limite.
- Ajouter un cache local avant de multiplier les sources.
- Ajouter un delai entre requetes si scraping web public.
- Garder une sortie stable meme si une source change son HTML.
- Tester la normalisation et les filtres sans dependance reseau.
- Isoler les appels externes dans des connecteurs.

## Premier endpoint vise

`POST /jobs/search`

Le backend recevra les filtres, interrogera les connecteurs actives, normalisera les offres, puis retournera une liste stable pour le futur front.
