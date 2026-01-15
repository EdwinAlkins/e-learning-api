# API Documentation

## Authentification

Tous les endpoints (sauf `/auth` et `/formations`) nécessitent le header :
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

### Progress

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

**DELETE** `/notes/{note_id}`
- Paramètres:
  - `note_id` (path): ID de la note
- Headers requis: `X-User-UID`
- Réponse: 204 No Content
