"""Точка входа TaskBoard: объект приложения FastAPI.

Все маршруты объявлены декораторами прямо на объекте ``app`` со статическими
строковыми путями. Подключение роутеров (include_router), динамическая
регистрация маршрутов и mount под статический профиль исследования
SecurityLab не подпадают, поэтому в приложении не используются.
"""

from typing import Any, Dict, Optional, Set

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .identity import get_current_user
from .store import BOARDS, COMMENTS, TASKS, TASK_STATUSES, USERS, next_id

app = FastAPI(
    title="TaskBoard",
    version="1.0.1",
    description="Demo target application for SecurityLab: boards, tasks, comments.",
)


class BoardIn(BaseModel):
    name: str


class MemberIn(BaseModel):
    username: str


class TaskIn(BaseModel):
    title: str
    description: str = ""
    assignee: Optional[str] = None


class TaskPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None


class CommentIn(BaseModel):
    body: str


# --- внутренние помощники -----------------------------------------------


def _deny(code: int, detail: str) -> None:
    raise HTTPException(status_code=code, detail=detail)


def _role(user: str) -> str:
    return USERS[user]["role"]


def _is_manager_or_admin(user: str) -> bool:
    return _role(user) in ("manager", "admin")


def _visible_board_ids(user: str) -> Set[str]:
    if _is_manager_or_admin(user):
        return set(BOARDS.keys())
    return {
        board_id
        for board_id, board in BOARDS.items()
        if board["owner"] == user or user in board["members"]
    }


def _board_member(user: str, board: Dict[str, Any]) -> bool:
    return user == board["owner"] or user in board["members"]


def _board_or_404(board_id: str) -> Dict[str, Any]:
    board = BOARDS.get(board_id)
    if board is None:
        _deny(404, "board not found")
    return board


def _visible_board(user: str, board_id: str) -> Dict[str, Any]:
    board = _board_or_404(board_id)
    if board_id not in _visible_board_ids(user):
        _deny(403, "board access denied")
    return board


def _task_or_404(task_id: str) -> Dict[str, Any]:
    task = TASKS.get(task_id)
    if task is None:
        _deny(404, "task not found")
    return task


def _visible_task(user: str, task_id: str) -> Dict[str, Any]:
    task = _task_or_404(task_id)
    _visible_board(user, task["board_id"])
    return task


def _board_view(board: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": board["id"],
        "name": board["name"],
        "owner": board["owner"],
        "members": list(board["members"]),
    }


def _task_view(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": task["id"],
        "board_id": task["board_id"],
        "title": task["title"],
        "description": task["description"],
        "status": task["status"],
        "assignee": task["assignee"],
        "created_by": task["created_by"],
    }


def _comment_view(comment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": comment["id"],
        "task_id": comment["task_id"],
        "author": comment["author"],
        "body": comment["body"],
    }


# --- доски ----------------------------------------------------------------


@app.get("/boards")
def list_boards(user: str = Depends(get_current_user)):
    visible = _visible_board_ids(user)
    return {"boards": [_board_view(BOARDS[bid]) for bid in sorted(visible)]}


@app.post("/boards", status_code=201)
def create_board(payload: BoardIn, user: str = Depends(get_current_user)):
    board_id = next_id("board")
    board = {"id": board_id, "name": payload.name, "owner": user, "members": [user]}
    BOARDS[board_id] = board
    return _board_view(board)


@app.get("/boards/{board_id}")
def get_board(board_id: str, user: str = Depends(get_current_user)):
    return _board_view(_visible_board(user, board_id))


@app.post("/boards/{board_id}/members", status_code=201)
def add_board_member(
    board_id: str, payload: MemberIn, user: str = Depends(get_current_user)
):
    board = _board_or_404(board_id)
    if user != board["owner"] and _role(user) != "admin":
        _deny(403, "only the board owner or admin can manage members")
    if payload.username not in USERS:
        _deny(404, "user not found")
    if payload.username in board["members"]:
        _deny(400, "user is already a board member")
    board["members"].append(payload.username)
    return _board_view(board)


@app.delete("/boards/{board_id}/members/{username}", status_code=204)
def remove_board_member(
    board_id: str, username: str, user: str = Depends(get_current_user)
):
    board = _board_or_404(board_id)
    if user != board["owner"] and _role(user) != "admin":
        _deny(403, "only the board owner or admin can manage members")
    if username == board["owner"]:
        _deny(400, "the board owner cannot be removed")
    if username not in board["members"]:
        _deny(404, "user is not a board member")
    board["members"].remove(username)


# --- задачи ----------------------------------------------------------------


@app.get("/boards/{board_id}/tasks")
def list_board_tasks(board_id: str, user: str = Depends(get_current_user)):
    _visible_board(user, board_id)
    tasks = [_task_view(t) for t in TASKS.values() if t["board_id"] == board_id]
    return {"tasks": tasks}


@app.post("/boards/{board_id}/tasks", status_code=201)
def create_task(
    board_id: str, payload: TaskIn, user: str = Depends(get_current_user)
):
    board = _visible_board(user, board_id)
    if not _board_member(user, board) and not _is_manager_or_admin(user):
        _deny(403, "only board members, manager or admin can create tasks")
    if payload.assignee is not None and payload.assignee not in board["members"]:
        _deny(400, "assignee must be a board member")
    task_id = next_id("task")
    task = {
        "id": task_id,
        "board_id": board_id,
        "title": payload.title,
        "description": payload.description,
        "status": "todo",
        "assignee": payload.assignee,
        "created_by": user,
    }
    TASKS[task_id] = task
    return _task_view(task)


@app.get("/tasks/{task_id}")
def get_task(task_id: str, user: str = Depends(get_current_user)):
    return _task_view(_visible_task(user, task_id))


@app.get("/my/tasks")
def my_tasks(user: str = Depends(get_current_user)):
    tasks = [_task_view(t) for t in TASKS.values() if t["assignee"] == user]
    return {"tasks": tasks}


@app.patch("/tasks/{task_id}")
def update_task(
    task_id: str, payload: TaskPatch, user: str = Depends(get_current_user)
):
    task = _visible_task(user, task_id)
    board = BOARDS[task["board_id"]]
    allowed = (
        user == task["assignee"]
        or user == board["owner"]
        or _is_manager_or_admin(user)
    )
    if not allowed:
        _deny(403, "task update denied")
    if payload.status is not None and payload.status not in TASK_STATUSES:
        _deny(400, "unknown status")
    if payload.assignee is not None and payload.assignee not in board["members"]:
        _deny(400, "assignee must be a board member")
    if payload.title is not None:
        task["title"] = payload.title
    if payload.description is not None:
        task["description"] = payload.description
    if payload.status is not None:
        task["status"] = payload.status
    if payload.assignee is not None:
        task["assignee"] = payload.assignee
    return _task_view(task)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, user: str = Depends(get_current_user)):
    task = _visible_task(user, task_id)
    board = BOARDS[task["board_id"]]
    allowed = (
        user == task["created_by"]
        or user == board["owner"]
        or _is_manager_or_admin(user)
    )
    if not allowed:
        _deny(403, "task delete denied")
    TASKS.pop(task_id, None)
    for comment_id in [
        cid for cid, c in COMMENTS.items() if c["task_id"] == task_id
    ]:
        COMMENTS.pop(comment_id, None)


# --- комментарии -----------------------------------------------------------


@app.get("/tasks/{task_id}/comments")
def list_task_comments(task_id: str, user: str = Depends(get_current_user)):
    _visible_task(user, task_id)
    comments = [
        _comment_view(c) for c in COMMENTS.values() if c["task_id"] == task_id
    ]
    return {"comments": comments}


@app.post("/tasks/{task_id}/comments", status_code=201)
def create_comment(
    task_id: str, payload: CommentIn, user: str = Depends(get_current_user)
):
    task = _visible_task(user, task_id)
    board = BOARDS[task["board_id"]]
    if not _board_member(user, board) and not _is_manager_or_admin(user):
        _deny(403, "only board members, manager or admin can comment")
    comment_id = next_id("comment")
    comment = {
        "id": comment_id,
        "task_id": task_id,
        "author": user,
        "body": payload.body,
    }
    COMMENTS[comment_id] = comment
    return _comment_view(comment)


@app.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: str, user: str = Depends(get_current_user)):
    comment = COMMENTS.get(comment_id)
    if comment is None:
        _deny(404, "comment not found")
    _visible_task(user, comment["task_id"])
    allowed = user == comment["author"] or _is_manager_or_admin(user)
    if not allowed:
        _deny(403, "comment delete denied")
    COMMENTS.pop(comment_id, None)


# --- справочник --------------------------------------------------------------


@app.get("/users")
def list_users(user: str = Depends(get_current_user)):
    return {"users": [dict(USERS[name]) for name in sorted(USERS)]}
