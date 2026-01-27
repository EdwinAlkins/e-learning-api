# Formation Backend

Backend API pour une plateforme de formation vidéo, développé avec FastAPI.

## Fonctionnalités

- **Authentification** : Génération d'UID utilisateur
- **Catalogue** : Gestion des formations, chapitres et vidéos
- **Streaming vidéo** : Diffusion avec support du seeking (Range requests)
- **Progression** : Suivi de la position de lecture par utilisateur
- **Notes** : Prise de notes avec timecode pour chaque vidéo

## Prérequis

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (gestionnaire de dépendances)
- FFmpeg (pour la conversion des vidéos)

## Installation

```bash
# Cloner le projet
git clone <repository-url>
cd formation-backend

# Installer les dépendances
uv sync
```

## Configuration

Les paramètres peuvent être configurés via des variables d'environnement ou un fichier `.env` :

- `DATABASE_PATH` : Chemin vers la base de données SQLite (défaut: `database.db`)
- `VIDEOS_PATH` : Répertoire contenant les vidéos (défaut: `videos/`)
- `LOG_LEVEL` : Niveau de logging (défaut: `INFO`)
- `DEBUG` : Mode debug (défaut: `False`)

## Utilisation

### Lancer l'API

```bash
uv run fastapi dev src/api/fastapi_app.py
uv run src.api
```

L'API sera accessible sur `http://localhost:8000` avec la documentation interactive sur `http://localhost:8000/docs`.

### Migrations de base de données

```bash
# Créer une nouvelle migration
uv run alembic revision --autogenerate -m "description"

# Appliquer les migrations
uv run alembic upgrade head
```

### Conversion des vidéos

```bash
uv run python -m src.scripts.convert_videos --help
```

### Transcrire les vidéos

```bash
uv run python -m src.scripts.transcribe --help
```

### Résumer les vidéos

```bash
uv run python -m src.scripts.resume --help
```

## Docker

### Construction de l'image

```bash
docker build -t formation-backend .
```

### Exécution avec montage de la base de données existante

Pour utiliser une base de données SQLite existante avec Docker, vous pouvez monter le fichier de base de données et son répertoire parent comme volume :

```bash
# Exemple : monter une base de données existante depuis le répertoire courant
docker run -d \
  --name formation-backend \
  -p 8000:8000 \
  -v $(pwd)/database.db:/app/data/database.db \
  -v $(pwd)/videos:/app/videos \
  -e DATABASE_PATH=/app/data/database.db \
  -e VIDEOS_PATH=/app/videos \
  formation-backend
```

**Explication des volumes :**
- `-v $(pwd)/database.db:/app/data/database.db` : Monte votre fichier de base de données existant dans le conteneur
- `-v $(pwd)/videos:/app/videos` : Monte le répertoire des vidéos
- `-e DATABASE_PATH=/app/data/database.db` : Configure le chemin de la base de données dans le conteneur
- `-e VIDEOS_PATH=/app/videos` : Configure le chemin des vidéos dans le conteneur

**Alternative : monter un répertoire complet**

Si vous préférez monter un répertoire complet contenant la base de données :

```bash
docker run -d \
  --name formation-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/videos:/app/videos \
  -e DATABASE_PATH=/app/data/database.db \
  -e VIDEOS_PATH=/app/videos \
  formation-backend
```

L'API sera accessible sur `http://localhost:8000` avec la documentation interactive sur `http://localhost:8000/docs`.

### Notes de sécurité

Le Dockerfile est configuré pour suivre les bonnes pratiques de sécurité :
- Utilisation d'un utilisateur non-root (`appuser`) pour l'exécution
- Image minimale basée sur `python:3.13-slim-bookworm`
- Nettoyage des caches apt pour réduire la taille de l'image
- Variables d'environnement pour optimiser Python

## Documentation

La documentation détaillée de l'API est disponible dans [`API.md`](API.md).

Une documentation complète sera disponible dans le répertoire `docs/` (à venir).

## Structure du projet

```
src/
├── api/              # Application FastAPI et routes
├── crud/             # Opérations CRUD
├── database/         # Modèles et schémas SQLAlchemy
├── services/         # Services métier
└── config.py         # Configuration
```
