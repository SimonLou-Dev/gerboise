# Brief — gerboise : bot Discord pilotable par API

## Contexte
Ce repo est un nouveau projet, indépendant de `home-lab`. Il doit produire un service
Python unique (un process) qui :
1. Maintient une connexion "gateway" vers Discord (bot classique, pas une app
   d'interactions HTTP) — ça évite d'avoir à exposer un port entrant : les clics de
   bouton arrivent via la connexion sortante du bot.
2. Expose une API HTTP interne (FastAPI) permettant à un appelant externe (aujourd'hui
   un workflow n8n, potentiellement d'autres choses plus tard) de poster des messages
   Discord avec boutons, sans jamais connaître le token du bot ni la mécanique Discord.

Le besoin déclencheur : un workflow n8n veut notifier une liste de mises à jour
d'apps en attente sur Discord, avec un bouton qui, une fois cliqué, doit relancer
ce même workflow n8n (y compris depuis un téléphone qui n'est pas connecté au VPN
de la maison). Mais l'API doit rester **générique** : ne pas câbler quoi que ce
soit de spécifique à ce cas d'usage dans ce repo.

## Stack imposée
- Python 3.12+, FastAPI (API), `discord.py` (bot gateway) — un seul process asyncio
  (FastAPI tourne dans le même event loop que le bot, via `discord.py` + `uvicorn`
  lancés ensemble, ou un lifespan FastAPI qui démarre le bot en tâche de fond).
- **SQLite** pour la persistance (pas de Postgres/Redis — c'est un service mono-instance
  à état minimal). Utiliser `aiosqlite` ou `sqlite3` + un lock, au choix, mais rester
  async-friendly puisque FastAPI/discord.py sont asyncio.
- Le fichier SQLite doit vivre dans un chemin configurable par variable d'env
  (ex. `DB_PATH=/data/gerboise.db`), pour pouvoir être monté comme volume une fois
  conteneurisé (le contenu ne doit pas être perdu à chaque redéploiement).

## Modèle de données (SQLite)
Une table suffit pour la v1, ex. `buttons` :
- `message_id` (clé Discord du message)
- `custom_id` (clé du bouton, unique par message)
- `callback_url` (où relayer le clic)
- `created_at`

## API à exposer
Toutes les routes sauf la racine/healthcheck sont protégées par une clé API statique
partagée, passée en header (ex. `Authorization: Bearer <API_KEY>`), comparée à la
variable d'env `API_KEY`. Pas d'auth multi-utilisateur, un seul appelant de confiance
à la fois (LAN interne).

- `GET /healthz` — pas d'auth, retourne 200 si le bot est connecté au gateway Discord.
- `POST /messages`
  - Body : `channel_id`, `content` (texte du message), `buttons` (liste de
    `{label, custom_id, callback_url}`, 0 à 5 boutons pour la v1, tous de type
    "action" — pas des boutons de type Link).
  - Poste le message dans le channel via le bot, enregistre chaque `(message_id,
    custom_id, callback_url)` en base.
  - Retourne `{"message_id": "..."}`.
- `PATCH /messages/{message_id}`
  - Body : nouveau `content` et/ou nouvelle liste de `buttons` (remplace les
    boutons existants — supprime les anciennes lignes SQLite pour ce message_id,
    insère les nouvelles).
  - Édite le message Discord en place.
- `DELETE /messages/{message_id}`
  - Supprime le message Discord + les lignes SQLite associées.
  - Idempotent : si le message n'existe déjà plus côté Discord (404 Discord), ne pas
    faire échouer l'appel, juste nettoyer la base et retourner 200.

## Relais des clics de bouton
Dans le handler d'interaction `discord.py` (`on_interaction` / listener
`component`) :
1. Répondre immédiatement à Discord par un accusé de réception (`interaction.response.
   defer()` ou message éphémère "⏳ en cours"), pour rester dans la fenêtre de 3s
   imposée par Discord.
2. Chercher en base le `callback_url` associé à `(message_id, custom_id)` de
   l'interaction cliquée.
3. Faire un `POST` HTTP vers ce `callback_url`, avec en body le payload utile :
   `{"message_id", "custom_id", "user": {"id", "username"}, "clicked_at"}`.
4. Pas de retry sophistiqué en v1 : un essai, logger l'erreur si le POST échoue
   (ne pas faire planter le bot).
5. Ne pas supprimer la ligne SQLite après le clic — un bouton peut être cliqué
   plusieurs fois (ex. retry) sauf si l'appelant supprime/édite explicitement le
   message ensuite via l'API.

## Configuration (variables d'env)
- `DISCORD_BOT_TOKEN` — token du bot (secret, jamais loggé).
- `API_KEY` — clé partagée pour l'API interne (secret).
- `DB_PATH` — chemin du fichier SQLite (défaut `/data/gerboise.db`).
- `LOG_LEVEL` — défaut `INFO`.

## Hors scope pour cette v1 (ne pas construire)
- Commandes slash Discord.
- Gestion de permissions par rôle.
- Multi-guild / multi-channel au-delà de ce que l'appelant précise par `channel_id`.
- Boutons de type "Link" (ouverture d'URL sans passer par le bot) — tous les
  boutons v1 sont des boutons d'action qui déclenchent le relais décrit plus haut.
- Authentification multi-utilisateur de l'API (une seule clé partagée suffit).

## CI/CD à mettre en place (GitHub Actions)
But : que chaque push sur `main` (et chaque tag `vX.Y.Z`) produise automatiquement
une image Docker publiée, prête à être référencée plus tard dans un autre repo
(`home-lab`) via une variable `discord_bot_docker_image` / `discord_bot_docker_tag`.

- Fichier `.github/workflows/build.yml` :
  - Trigger : `push` sur `main`, et `push` de tags `v*`.
  - Étapes : checkout, `docker/setup-buildx-action`, login au registre (GHCR via
    `GITHUB_TOKEN`, pas de secret supplémentaire à gérer), `docker/build-push-action`
    pour builder le `Dockerfile` à la racine et pousser :
    - `ghcr.io/<owner>/gerboise:latest` sur push `main`.
    - `ghcr.io/<owner>/gerboise:<tag>` sur push d'un tag `v*`.
  - Architecture cible : `linux/amd64` seul suffit (les hôtes du homelab visé sont
    amd64) — pas besoin de multi-arch pour l'instant.
  - Ajouter une étape de lint/test rapide avant le build (ex. `ruff check` +
    `pytest` si des tests existent) qui bloque le build si elle échoue.
- `Dockerfile` : image Python slim, installe les dépendances (`requirements.txt` ou
  `pyproject.toml` + `uv`/`pip`), copie le code, expose le port API (ex. 8080),
  déclare un volume anonyme pour `/data` (où vit le SQLite), `CMD` qui lance l'app
  (uvicorn + démarrage du bot dans le lifespan).

## Definition of done
- `docker run` de l'image (avec `DISCORD_BOT_TOKEN`/`API_KEY` fournis) démarre un bot
  visible "en ligne" dans un serveur Discord de test.
- `POST /messages` avec un bouton dont `callback_url` pointe vers un endpoint de test
  (ex. webhook.site ou un petit serveur local) : le message apparaît dans Discord,
  cliquer le bouton déclenche bien un `POST` vers ce `callback_url`.
- `PATCH` et `DELETE` fonctionnent sur un message existant.
- Un push sur `main` déclenche le workflow CI et produit une image visible dans
  les packages GHCR du repo.
- Redémarrer le conteneur ne perd pas les mappings `message_id -> callback_url`
  déjà enregistrés (volume SQLite persistant testé).
