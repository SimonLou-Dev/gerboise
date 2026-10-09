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

Chaque push sur `main` (et chaque tag `vX.Y.Z`) lance les tests + lint, puis publie
une image sur GHCR : `ghcr.io/<owner>/gerboise:latest` (main) ou
`ghcr.io/<owner>/gerboise:<version>` (tag).
