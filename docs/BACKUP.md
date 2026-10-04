# Backup and restore

Create (never includes model files unless --include-models):

    nexora backup create
    nexora backup create --include-models

Restore:

    nexora backup restore <archive.zip>
    nexora backup restore <archive.zip> --skip-db   # skills/workspaces only

Contents: SQLite DB, skills/, workspaces/, .env.example.
Archives are written to data/backups/.
