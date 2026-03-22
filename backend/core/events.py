"""
Event dispatch — routes fire named events, workers handle them.

This keeps routes decoupled from task internals: a route doesn't
import or call a specific task function, it just says "this happened"
and the handler registry decides what runs.
"""

from collections.abc import Callable

_handlers: dict[str, list] = {}


def on(event: str) -> Callable[[Callable], Callable]:
    """Decorator to register a Celery task as the handler for an event."""
    def decorator(task: Callable) -> Callable:
        _handlers.setdefault(event, []).append(task)
        return task
    return decorator


def dispatch(event: str, payload: dict | None = None) -> list[str]:
    """Fire an event and return the Celery task IDs that were enqueued."""
    task_ids = []
    for handler in _handlers.get(event, []):
        result = handler.delay(payload or {})
        task_ids.append(result.id)
    return task_ids
