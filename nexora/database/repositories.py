from sqlalchemy.orm import Session
from nexora.database.models import Base

def init_db(engine):
    Base.metadata.create_all(engine)

def session_factory(engine):
    def factory():
        return Session(engine)
    return factory
