"""Тестовая идентификация: заголовок X-Test-User.

Заголовок имитирует уже проверенную идентичность, приходящую от доверенного
шлюза. Это тестовая инфраструктура, а не производственный вход по паролю.
"""

from typing import Optional

from fastapi import Header, HTTPException

from .store import USERS


def get_current_user(x_test_user: Optional[str] = Header(default=None)) -> str:
    if not x_test_user:
        raise HTTPException(status_code=401, detail="missing identity header")
    if x_test_user not in USERS:
        raise HTTPException(status_code=401, detail="unknown identity")
    return x_test_user
