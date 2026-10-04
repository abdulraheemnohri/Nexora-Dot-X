from nexora.core.ws import hub


def test_broadcast_no_clients_is_safe():
    hub.broadcast("test.kind", {"a": 1})  # must not raise
