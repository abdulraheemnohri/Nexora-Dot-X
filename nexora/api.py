from nexora.database.runtime import SessionFactory
from nexora.database.models import Task
def task_json(t): return {"id":t.id,"dot_id":t.dot_id,"goal":t.goal,"status":t.status,"result":t.result}
def api_status(settings): return {"status":"ready","local_only":settings.local_only}
