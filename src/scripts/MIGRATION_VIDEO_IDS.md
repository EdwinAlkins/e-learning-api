# Migration des IDs de vidéos

## Description

Ce script permet de migrer les IDs de vidéos dans la base de données lors d'un changement de méthode de génération des IDs.

### Contexte

Les IDs de vidéos sont générés à partir du chemin du fichier vidéo en utilisant un hash SHA1. Il y a eu un changement dans la méthode de génération :

- **Ancien système** : ID basé sur le **chemin absolu** complet du fichier
- **Nouveau système** : ID basé sur le **chemin tronqué** (3 derniers niveaux seulement)

Ce changement permet d'avoir des IDs plus stables qui ne dépendent pas de l'emplacement absolu du répertoire de vidéos, mais uniquement de la structure relative (formation/chapitre/fichier).

### Problème résolu

Lors du changement de méthode de génération, les anciens IDs ne correspondent plus aux nouveaux IDs. Cela signifie que :
- Les commentaires (notes) associés aux vidéos sont perdus
- Les progrès de lecture des utilisateurs sont perdus

Ce script résout ce problème en :
1. Scannant tous les fichiers vidéo
2. Créant un mapping entre les anciens IDs et les nouveaux IDs
3. Mettant à jour automatiquement les tables `note` et `progress` dans la base de données

## Utilisation

### Prérequis

- Avoir une sauvegarde de la base de données (⚠️ **IMPORTANT**)
- Les fichiers vidéo doivent être accessibles dans le répertoire configuré (`VIDEOS_PATH`)
- Le script doit être exécuté depuis la racine du projet

### Commande

```bash
uv run python src/scripts/migrate_video_ids.py
```

### Configuration

Le script utilise la configuration définie dans `src/config.py`. Les paramètres suivants sont utilisés :

- `VIDEOS_PATH` : Répertoire contenant les vidéos (défaut: `videos/`)
- `DATABASE_PATH` : Chemin vers la base de données SQLite (défaut: `database.db`)
- `LOG_LEVEL` : Niveau de logging (défaut: `INFO`)

Ces paramètres peuvent être configurés via :
- Variables d'environnement
- Fichier `.env` à la racine du projet

### Exemple de sortie

```
2026-01-19 11:42:24,130 - INFO - ============================================================
2026-01-19 11:42:24,131 - INFO - Starting video ID migration
2026-01-19 11:42:24,132 - INFO - ============================================================
2026-01-19 11:42:24,133 - INFO - Videos path: /path/to/videos
2026-01-19 11:42:24,134 - INFO - Database path: database.db
2026-01-19 11:42:24,135 - INFO - Scanning videos directory: /path/to/videos
2026-01-19 11:42:25,200 - INFO - Found 150 videos, 150 ID mappings created
2026-01-19 11:42:25,201 - INFO - IDs that will change: 150 out of 150
2026-01-19 11:42:25,202 - INFO - Migrating notes...
2026-01-19 11:42:25,250 - INFO - Updated 45 notes
2026-01-19 11:42:25,251 - INFO - Migrating progress...
2026-01-19 11:42:25,300 - INFO - Updated 120 progress records
2026-01-19 11:42:25,301 - INFO - ============================================================
2026-01-19 11:42:25,302 - INFO - Migration summary:
2026-01-19 11:42:25,303 - INFO -   Notes updated: 45
2026-01-19 11:42:25,304 - INFO -   Notes not migrated: 0
2026-01-19 11:42:25,305 - INFO -   Progress updated: 120
2026-01-19 11:42:25,306 - INFO -   Progress not migrated: 0
2026-01-19 11:42:25,307 - INFO - ============================================================
2026-01-19 11:42:25,308 - INFO - ✅ Migration completed successfully!
```

## Fonctionnement technique

### Génération des IDs

#### Ancien système
```python
absolute_path = str(video_path.resolve())
old_id = hashlib.sha1(absolute_path.encode()).hexdigest()
```

Exemple :
- Chemin : `/home/user/videos/formation-python/chapitre-1/intro.mp4`
- ID : `a1b2c3d4e5f6...` (basé sur le chemin complet)

#### Nouveau système
```python
truncated_path = str(Path(*video_path.parts[-3:]))  # 3 derniers niveaux
new_id = hashlib.sha1(truncated_path.encode()).hexdigest()
```

Exemple :
- Chemin : `/home/user/videos/formation-python/chapitre-1/intro.mp4`
- Chemin tronqué : `formation-python/chapitre-1/intro.mp4`
- ID : `x9y8z7w6v5u4...` (basé sur le chemin tronqué)

### Processus de migration

1. **Scan des vidéos** : Le script parcourt récursivement le répertoire `VIDEOS_PATH` pour trouver tous les fichiers `.mp4`
2. **Création du mapping** : Pour chaque vidéo, il calcule l'ancien ID et le nouveau ID, puis crée un dictionnaire de correspondance
3. **Mise à jour des notes** : Tous les enregistrements de la table `note` sont mis à jour avec les nouveaux IDs
4. **Mise à jour des progrès** : Tous les enregistrements de la table `progress` sont mis à jour avec les nouveaux IDs
5. **Validation** : Le script affiche un résumé des migrations effectuées

### Tables affectées

- **`note`** : Table contenant les commentaires/notes des utilisateurs avec timecode
  - Champ modifié : `video_id`
  
- **`progress`** : Table contenant la progression de lecture des utilisateurs
  - Champ modifié : `video_id`

## Cas d'erreur

### Vidéos non trouvées

Si un `video_id` dans la base de données ne correspond à aucun fichier vidéo scanné, le script :
- Affiche un avertissement pour chaque enregistrement non migré
- Continue la migration pour les autres enregistrements
- Compte le nombre d'enregistrements non migrés dans le résumé

Cela peut arriver si :
- Des vidéos ont été supprimées depuis la création des notes/progrès
- Le répertoire de vidéos a été déplacé ou réorganisé
- Des fichiers vidéo ont été renommés ou déplacés

### Aucun changement nécessaire

Si tous les IDs sont déjà au nouveau format (ce qui ne devrait pas arriver lors d'une première migration), le script affiche :
```
No IDs need to be migrated. All IDs are already using the new format.
```

## Sécurité et sauvegarde

⚠️ **IMPORTANT** : Ce script modifie directement la base de données. Il est **fortement recommandé** de faire une sauvegarde avant d'exécuter le script.

### Sauvegarde de la base de données

```bash
# Copie simple
cp database.db database.db.backup

# Ou avec timestamp
cp database.db database.db.backup.$(date +%Y%m%d_%H%M%S)
```

### Rollback

En cas de problème, vous pouvez restaurer la base de données depuis la sauvegarde :

```bash
cp database.db.backup database.db
```

## Dépannage

### Le script ne trouve aucune vidéo

Vérifiez que :
- Le paramètre `VIDEOS_PATH` est correctement configuré
- Le répertoire existe et contient des fichiers `.mp4`
- Les fichiers vidéo sont organisés en `formation/chapitre/video.mp4`

### Erreurs de connexion à la base de données

Vérifiez que :
- Le paramètre `DATABASE_PATH` est correct
- Le fichier de base de données existe
- Vous avez les permissions de lecture/écriture sur le fichier

### Logs détaillés

Pour obtenir plus de détails sur le processus de migration, vous pouvez augmenter le niveau de logging :

```bash
LOG_LEVEL=DEBUG uv run python src/scripts/migrate_video_ids.py
```

## Notes

- Le script est **idempotent** : il peut être exécuté plusieurs fois sans problème
- Les IDs qui n'ont pas changé ne sont pas modifiés
- Le script utilise une transaction : en cas d'erreur, toutes les modifications sont annulées (rollback)
