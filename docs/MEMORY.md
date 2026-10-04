# Memory & Federation

Nexora memory runs on SQLite with layers: working, episodic, semantic,
procedural, user, project, skill.

## Federated search
`MemoryService.search()` queries all layers, then the `Federation` resolver
dedupes conflicting records. Priority: manual approval > trusted source >
confidence > recency.

## UI
- `/memory` — search box (HTMX), add-memory form
- `POST /api/memory/search` — returns merged, deduped results
- `POST /api/memory/remember` — save new memory

## API
```bash
curl -X POST http://127.0.0.1:8000/api/memory/search -d "query=preferences"
```
