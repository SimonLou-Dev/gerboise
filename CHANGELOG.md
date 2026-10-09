# CHANGELOG


## v0.1.1 (2026-10-09)

### Bug Fixes

- Install curl for healthcheck, validate Discord IDs, constant-time token check
  ([`9964c36`](https://github.com/SimonLou-Dev/gerboise/commit/9964c361cfd15dd4aef83a3357ce52e6bce5e606))

- Dockerfile: install curl (python:3.14-slim has neither wget nor curl by default, which made the
  Ansible-side liveness probe fail its exec and restart-loop the container) - discord_bot.py:
  validate channel_id/message_id as proper snowflakes and catch discord.NotFound/Forbidden in
  post_message/edit_message/create_thread, returning clean 422/404/403 instead of an unhandled 500
  (delete_message already did this, the others didn't) - security.py: compare the bearer token with
  hmac.compare_digest instead of != to avoid a timing side-channel

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>


## v0.1.0 (2026-10-09)

### Features

- Add embeds, thread creation, slash command and automated releases
  ([`75b66ae`](https://github.com/SimonLou-Dev/gerboise/commit/75b66aeacd3bf26e82410bd7aa6505a5f9358dd2))

- Messages peuvent désormais inclure un embed Discord (titre, description, couleur, champs, footer,
  auteur, images) en plus du contenu texte et des boutons, sur POST et PATCH /messages. - Nouvel
  endpoint POST /messages/{message_id}/threads : crée un thread Discord sur un message existant et
  renvoie son thread_id, réutilisable comme channel_id dans POST /messages pour y poster des logs
  (pas de nouvel endpoint de postage, API générique conservée). - Ajout de l'infra slash commands
  (discord.app_commands.CommandTree sur le Client existant) avec une première commande /status ;
  sync instantanée si DISCORD_GUILD_ID est renseigné, sync globale sinon. - CI : ajout de
  python-semantic-release pour automatiser le versioning à partir des commits conventionnels
  (feat:/fix:/...) sur push main — bump pyproject.toml + CHANGELOG.md + tag vX.Y.Z, qui déclenche la
  publication de l'image taguée en plus du :latest systématique.

Testé en conditions réelles sur un serveur Discord de test : embed affiché correctement, thread créé
  + log posté dedans, bouton cliqué relayé.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
