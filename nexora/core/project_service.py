from nexora.database.models import Artifact, Message, Project, Session
from nexora.database import repositories as repo


class ProjectService:
    def create(self, name: str, description: str = "", workspace: str = ""):
        return repo.add_obj(Project(name=name, description=description, workspace=workspace))

    def get(self, project_id: str):
        return repo.get_by_id(Project, project_id)

    def list(self):
        return repo.get_all(Project, order_desc="created_at")


class SessionService:
    def create(self, project_id: str | None = None, dot_id: str | None = None, title: str = ""):
        return repo.add_obj(Session(project_id=project_id, dot_id=dot_id, title=title))

    def get(self, session_id: str):
        return repo.get_by_id(Session, session_id)

    def messages(self, session_id: str, limit: int = 200):
        return repo.query(Message, Message.session_id == session_id, limit=limit)

    def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None):
        import json
        return repo.add_obj(Message(
            session_id=session_id, role=role, content=content,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        ))

    def close(self, session_id: str):
        return repo.update_fields(repo.get_by_id(Session, session_id), status="closed")


class ArtifactService:
    def create(self, name: str, *, project_id: str | None = None,
               task_id: str | None = None, session_id: str | None = None,
               kind: str = "file", path: str = "", content: str = "",
               checksum: str = "", metadata: dict | None = None):
        import json
        return repo.add_obj(Artifact(
            name=name, project_id=project_id, task_id=task_id,
            session_id=session_id, kind=kind, path=path, content=content,
            checksum=checksum,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        ))

    def get(self, artifact_id: str):
        return repo.get_by_id(Artifact, artifact_id)

    def list_for_task(self, task_id: str):
        return repo.query(Artifact, Artifact.task_id == task_id, limit=1000)
