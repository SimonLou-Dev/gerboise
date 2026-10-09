# gerboise

Bot Discord pilotable par API HTTP interne. Un seul process asyncio : une connexion
gateway Discord (`discord.py`) et une API FastAPI qui permet à un appelant externe
(ex. un workflow n8n) de poster/éditer/supprimer des messages Discord avec boutons,
et de relayer les clics vers une `callback_url` fournie par l'appelant. Voir
`AGENT_BRIEF.md` pour le détail du besoin.

## Prérequis

- Python 3.14 (ou toute version `>=3.13,<4.0`)
- [Poetry](https://python-poetry.org/) 2.x

## Développement local

```bash
poetry install
cp .env.example .env   # puis renseigner DISCORD_BOT_TOKEN et API_KEY
poetry run pre-commit install
poetry run uvicorn gerboise.main:app --reload --port 8080
```

Génération d'une `API_KEY` aléatoire :

```bash
openssl rand -hex 32
```

### Tests et lint

```bash
poetry run pytest
poetry run ruff check .
poetry run ruff format .
poetry run pre-commit run --all-files
```

## Variables d'environnement

| Variable             | Défaut              | Description                                  |
|-----------------------|----------------------|-----------------------------------------------|
| `DISCORD_BOT_TOKEN`  | *(requis)*           | Token du bot Discord (secret).                 |
| `API_KEY`            | *(requis)*           | Clé partagée pour l'API interne (secret).      |
| `DB_PATH`            | `/data/gerboise.db`  | Chemin du fichier SQLite.                      |
| `LOG_LEVEL`          | `INFO`                | Niveau de log.                                 |

## API

Toutes les routes sauf `GET /healthz` nécessitent l'en-tête
`Authorization: Bearer <API_KEY>`.

- `GET /healthz` — 200 si le bot est connecté au gateway Discord.
- `POST /messages` — poste un message avec 0 à 5 boutons d'action.
- `PATCH /messages/{message_id}` — édite le contenu et/ou remplace les boutons.
- `DELETE /messages/{message_id}` — supprime le message (idempotent).

## Docker

```bash
docker build -t gerboise .
docker run -d \
  -e DISCORD_BOT_TOKEN=... \
  -e API_KEY=... \
  -p 8080:8080 \
  -v gerboise-data:/data \
  gerboise
```

Le volume `/data` doit être persistant pour ne pas perdre les mappings
`message_id -> callback_url` entre deux redémarrages.

## CI/CD

Chaque push sur `main` lance les tests + lint, puis :

1. [python-semantic-release](https://python-semantic-release.readthedocs.io/) analyse
   les commits depuis la dernière release. S'il trouve des commits
   [conventionnels](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
   `perf:`, `BREAKING CHANGE:`...), il bump la version dans `pyproject.toml`,
   met à jour `CHANGELOG.md`, commit, crée le tag `vX.Y.Z` et le pousse sur `main`.
2. L'image Docker est buildée et publiée sur GHCR :
   `ghcr.io/<owner>/gerboise:latest` toujours, et
   `ghcr.io/<owner>/gerboise:<version>` si une release a eu lieu à l'étape 1.

Sans commit `feat:`/`fix:` (etc.) depuis la dernière release, seul `:latest` est
republié — pas de nouvelle version taguée.
