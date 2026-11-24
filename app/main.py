"""Точка входа TaskBoard: объект приложения FastAPI."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="TaskBoard",
    version="1.0.0",
    description="Demo target application for SecurityLab: boards, tasks, comments.",
)

app.include_router(router)
