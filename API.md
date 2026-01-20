# API Documentation

## Authentification

Tous les endpoints (sauf `/auth`, `/formations` et `/videos`) nécessitent le header :
```
X-User-UID: <uid>
```

## Endpoints

### Healthcheck

**GET** `/`
- Aucun paramètre
- Réponse: `{"message": "health ok"}`

### Auth

**POST** `/auth/generate`
- Aucun paramètre
- Réponse: `{"uid": "string"}` (64 caractères hex)

### Formations

**GET** `/formations`
- Aucun paramètre
- Réponse: Catalogue complet (formations, chapitres, vidéos)

### Videos

**GET** `/videos/{video_id}/stream`
- Paramètres:
  - `video_id` (path): SHA1 hash du chemin de la vidéo
- Headers optionnels:
  - `Range: bytes=start-end` (pour le seeking)
- Réponse: Stream vidéo (206 Partial Content ou 200 OK)

**GET** `/videos/{video_id}/file`
- Paramètres:
  - `video_id` (path): SHA1 hash du chemin de la vidéo
- Réponse: Fichier vidéo en téléchargement

**GET** `/videos/{video_id}/summary`
- Paramètres:
  - `video_id` (path): SHA1 hash du chemin de la vidéo
- Réponse: `{"summary": "string"}` (résumé en format Markdown)
- Erreurs:
  - `404`: Si la vidéo n'existe pas ou si le résumé n'est pas disponible

**PUT** `/videos/{video_id}/summary`
- Paramètres:
  - `video_id` (path): SHA1 hash du chemin de la vidéo
- Body: `{"summary": "string"}` (nouveau résumé en format Markdown)
- Réponse: `{"summary": "string"}` (résumé mis à jour)
- Erreurs:
  - `404`: Si la vidéo n'existe pas ou si le résumé n'existe pas encore (il doit être créé d'abord)

### Progress

**GET** `/progress/formation/{formation_name}`
- Paramètres:
  - `formation_name` (path): Nom de la formation
- Headers requis: `X-User-UID`
- Réponse: Objet avec l'avancement de la formation, de chaque chapitre et de chaque vidéo
  ```json
  {
    "name": "string",
    "chapters": [
      {
        "name": "string",
        "videos": [
          {
            "id": "string",
            "title": "string",
            "progress_percentage": float
          }
        ],
        "progress_percentage": float
      }
    ],
    "progress_percentage": float
  }
  ```

**GET** `/progress/{video_id}`
- Paramètres:
  - `video_id` (path): ID de la vidéo
- Headers requis: `X-User-UID`
- Réponse: `{"last_position": float}`

**POST** `/progress/{video_id}`
- Paramètres:
  - `video_id` (path): ID de la vidéo
- Headers requis: `X-User-UID`
- Body: `{"last_position": float}`
- Réponse: `{"last_position": float}`

### Notes

**GET** `/notes/{video_id}`
- Paramètres:
  - `video_id` (path): ID de la vidéo
- Headers requis: `X-User-UID`
- Réponse: `[{"id": int, "video_id": "string", "timecode": float, "content": "string", "created_at": "datetime"}]`

**POST** `/notes/{video_id}`
- Paramètres:
  - `video_id` (path): ID de la vidéo
- Headers requis: `X-User-UID`
- Body: `{"timecode": float, "content": "string"}`
- Réponse: `{"id": int, "video_id": "string", "timecode": float, "content": "string", "created_at": "datetime"}`

**PUT** `/notes/{note_id}`
- Paramètres:
  - `note_id` (path): ID de la note
- Headers requis: `X-User-UID`
- Body: `{"content": "string"}`
- Réponse: `{"id": int, "video_id": "string", "timecode": float, "content": "string", "created_at": "datetime"}`

**DELETE** `/notes/{note_id}`
- Paramètres:
  - `note_id` (path): ID de la note
- Headers requis: `X-User-UID`
- Réponse: 204 No Content
