"""Repository pattern helpers over the SQLAlchemy session factory."""
from typing import Any, Iterable
from sqlalchemy import select
from nexora.database.engine import get_session_factory


def _session():
    return get_session_factory()()


def add_obj(obj: Any) -> Any:
    with _session() as s:
        s.add(obj)
        s.commit()
        s.refresh(obj)
        return obj


def get_all(model: type, *, limit: int = 200, order_desc: str | None = None) -> list:
    with _session() as s:
        q = select(model).limit(limit)
        if order_desc:
            q = q.order_by(getattr(model, order_desc).desc())
        return list(s.scalars(q))


def get_by_id(model: type, id_: str):
    with _session() as s:
        return s.get(model, id_)


def update_fields(obj: Any, **fields) -> Any:
    with _session() as s:
        o = s.merge(obj)
        for k, v in fields.items():
            setattr(o, k, v)
        s.commit()
        s.refresh(o)
        return o


def delete_by_id(model: type, id_: str) -> bool:
    with _session() as s:
        o = s.get(model, id_)
        if o is None:
            return False
        s.delete(o)
        s.commit()
        return True


def query(model: type, *conditions, limit: int = 200) -> Iterable:
    with _session() as s:
        q = select(model)
        for c in conditions:
            q = q.where(c)
        return list(s.scalars(q.limit(limit)))
