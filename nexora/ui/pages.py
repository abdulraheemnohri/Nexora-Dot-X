"""Lightweight page helpers shared across UI modules."""
from fasthtml.common import Titled, H1, P


def page(title: str, *body):
    return Titled(title, H1(title), P("Nexora Dot X"), *body)
