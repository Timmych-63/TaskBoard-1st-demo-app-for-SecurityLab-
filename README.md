# TaskBoard — первое демо-приложение-цель для SecurityLab

Маленькое настоящее приложение: доска задач с ролями (boards → tasks → comments).
Написано как цель-приложение №1 для SecurityLab v0.1.0 под текущий профиль ядра:
FastAPI, данные в памяти, вход через тестовый заголовок `X-Test-User`.

## Акторы

| Пользователь | Роль    |
|--------------|---------|
| alice        | user    |
| bob          | user    |
| mira         | manager |
| admin        | admin   |

## Маршруты (15)

- Доски: `GET /boards`, `POST /boards`, `GET /boards/{board_id}`, `POST /boards/{board_id}/members`, `DELETE /boards/{board_id}/members/{username}`
- Задачи: `GET /boards/{board_id}/tasks`, `POST /boards/{board_id}/tasks`, `GET /tasks/{task_id}`, `GET /my/tasks`, `PATCH /tasks/{task_id}`, `DELETE /tasks/{task_id}`
- Комментарии: `GET /tasks/{task_id}/comments`, `POST /tasks/{task_id}/comments`, `DELETE /comments/{comment_id}`
- Справочник: `GET /users`

## Файлы для SecurityLab

- `docs/taskboard.md` — база знаний приложения (ожидаемое поведение)
- `docs/taskboard.setup.json` — конфигурация стенда: акторы и бюджет

Формат тот же, что у AuthzNotes/TicketDesk (см. `examples/research` в SecurityLab).

## Структура репозитория

```
app/
  __init__.py
  main.py       # точка входа: объект app
  identity.py   # X-Test-User: 401 без заголовка или с неизвестным именем
  store.py      # данные в памяти + исходные тестовые данные
  routes.py     # все 15 маршрутов
docs/
  taskboard.md
  taskboard.setup.json
requirements.txt
pyproject.toml
```

Данные хранятся в памяти: при перезапуске приложения данные сбрасываются к исходным тестовым.

## Запуск

Зависимости совпадают с подготовленным образом FastAPI (fastapi==0.115.12, uvicorn==0.34.2).

Локально:

```
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

В контейнере securitylab-demo:local (из папки репозитория, PowerShell):

```
docker run --rm -p 8000:8000 -v "${PWD}:/srv" -w /srv securitylab-demo:local uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Быстрая проверка

```
curl -H "X-Test-User: alice" http://127.0.0.1:8000/boards      # 200, доска b1
curl -H "X-Test-User: mira" http://127.0.0.1:8000/boards       # 200, обе доски
curl http://127.0.0.1:8000/boards                              # 401
curl -H "X-Test-User: bob" http://127.0.0.1:8000/boards/b2     # 403
curl -H "X-Test-User: bob" http://127.0.0.1:8000/boards/b99    # 404
```

## Примечание

Приложение написано по правилам из `docs/taskboard.md`. Проверка ядром SecurityLab
должна находить нарушения только там, где они действительно есть.
