"""Хранилище TaskBoard в памяти: пользователи, доски, задачи, комментарии.

Каждая новая копия приложения получает исходные тестовые данные.
Внешняя база данных не требуется.
"""

from __future__ import annotations

import threading
from typing import Any, Dict

USERS: Dict[str, Dict[str, Any]] = {
    "alice": {"username": "alice", "role": "user", "display_name": "Alice"},
    "bob": {"username": "bob", "role": "user", "display_name": "Bob"},
    "mira": {"username": "mira", "role": "manager", "display_name": "Mira"},
    "admin": {"username": "admin", "role": "admin", "display_name": "Admin"},
}

BOARDS: Dict[str, Dict[str, Any]] = {
    "b1": {
        "id": "b1",
        "name": "Release 1.0",
        "owner": "alice",
        "members": ["alice", "bob"],
    },
    "b2": {
        "id": "b2",
        "name": "Internal Ops",
        "owner": "mira",
        "members": ["mira"],
    },
}

TASKS: Dict[str, Dict[str, Any]] = {
    "t1": {
        "id": "t1",
        "board_id": "b1",
        "title": "Write install guide",
        "description": "Step-by-step install guide for the release.",
        "status": "todo",
        "assignee": "bob",
        "created_by": "alice",
    },
    "t2": {
        "id": "t2",
        "board_id": "b1",
        "title": "Fix login page crash",
        "description": "Page crashes when username is empty.",
        "status": "in_progress",
        "assignee": "alice",
        "created_by": "alice",
    },
    "t3": {
        "id": "t3",
        "board_id": "b1",
        "title": "Prepare demo checklist",
        "description": "",
        "status": "done",
        "assignee": "bob",
        "created_by": "bob",
    },
    "t4": {
        "id": "t4",
        "board_id": "b2",
        "title": "Rotate access keys",
        "description": "Quarterly key rotation.",
        "status": "todo",
        "assignee": "mira",
        "created_by": "mira",
    },
}

COMMENTS: Dict[str, Dict[str, Any]] = {
    "c1": {"id": "c1", "task_id": "t1", "author": "bob", "body": "Draft started."},
    "c2": {"id": "c2", "task_id": "t2", "author": "alice", "body": "Reproduced the crash."},
    "c3": {"id": "c3", "task_id": "t4", "author": "mira", "body": "Scheduled for Friday."},
}

TASK_STATUSES = ("todo", "in_progress", "done")

_lock = threading.Lock()
_counters = {
    "board": len(BOARDS),
    "task": len(TASKS),
    "comment": len(COMMENTS),
}
_PREFIX = {"board": "b", "task": "t", "comment": "c"}


def next_id(kind: str) -> str:
    """Новый идентификатор сущности: b3, t5, c4 и так далее."""
    with _lock:
        _counters[kind] += 1
        return "%s%d" % (_PREFIX[kind], _counters[kind])
