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
uv run python convert_videos.py
```

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
