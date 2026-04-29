# Modele agentique d'extraction des competences

## Objectif

Extraire les competences demandees par le marche a partir des offres collectees, en conservant le lien avec :

- le mot-cle ou intitule de recherche
- l'offre source
- la societe
- les preuves textuelles

## Architecture courte

Le backend orchestre plusieurs petits agents specialises :

- `llm_candidate_extractor` : appelle un petit LLM local pour extraire les competences candidates.
- `candidate_extractor` : fallback deterministe si le LLM local n'est pas configure ou pas lance.
- `normalizer` : dedoublonne et harmonise les competences.
- `verifier` : filtre par confiance, regroupe les preuves, et produit une sortie stable.

Le backend ne charge pas le modele dans son propre process. Il appelle un serveur local OpenAI-compatible via HTTP.
Quand le serveur local est stoppe, le GPU AMD est libere par ce serveur, pas par FastAPI.

## Configuration LLM local

Variables d'environnement :

```powershell
$env:LOCAL_LLM_BASE_URL="http://localhost:1234"
$env:LOCAL_LLM_MODEL="qwen2.5-3b-instruct"
$env:LOCAL_LLM_TIMEOUT_SECONDS="45"
```

Le port `1234` correspond souvent au serveur local de LM Studio. Ollama, llama.cpp server ou Lemonade peuvent aussi etre utilises s'ils exposent une API compatible OpenAI.

Sur Windows avec GPU AMD, privilegier un serveur qui supporte Vulkan ou ROCm selon ta carte :

- LM Studio : simple pour tester, OpenAI-compatible, GPU offload configurable.
- Ollama : pratique pour gerer les modeles ; verifier que ta carte AMD est bien acceleree.
- llama.cpp server : robuste, backend Vulkan possible, plus manuel.

## Endpoint

`POST /competencies/extract`

Entrée :

```json
{
  "keyword": "data",
  "job_title": "Data Analyst",
  "offers": []
}
```

Sortie :

```json
{
  "run_id": "...",
  "competencies": [],
  "agent_trace": []
}
```

`agent_trace` permet de verifier quel agent a travaille et combien de candidates ont ete gardees.

## Stockage PostgreSQL

Le premier schema est dans :

- `migrations/001_competency_market_schema.sql`

Tables principales :

- `companies`
- `job_search_runs`
- `job_offers`
- `competencies`
- `competency_observations`

Les observations relient une competence a une offre, une societe et une recherche, avec un score de confiance et une preuve textuelle.

## Lancer PostgreSQL local

```powershell
docker compose up -d postgres
```

La base locale attendue par `.env.example` est :

```text
postgresql://agent_competence:agent_competence@localhost:5432/agent_competence
```

Au premier demarrage, Docker applique les fichiers dans `migrations/`.

## Analyser et sauvegarder

Depuis la config actuelle :

```powershell
python -m app.analyze_cli
```

ou :

```powershell
.\scripts\analyze-competencies.cmd
```

La commande :

1. charge `config/job_search_request.json`
2. reutilise le cache HTTP si les pages sont deja presentes
3. extrait les competences avec le LLM local si configure
4. fallback sur l'extracteur deterministe sinon
5. sauvegarde dans PostgreSQL si `DATABASE_URL` est renseigne

## Petit client SQL

Requete directe :

```powershell
python -m app.sql_client -q "select name, category from competencies order by name limit 20"
```

ou :

```powershell
.\scripts\query-db.cmd -q "select request_keyword, created_at from job_search_runs order by created_at desc limit 5"
```

Mode interactif :

```powershell
python -m app.sql_client
```
