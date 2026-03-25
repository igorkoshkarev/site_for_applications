import asyncio

import pytest
from fastapi import HTTPException

from app.applications.models import ApplicationStatus
from app.applications import router as app_router
from tests.conftest import make_request


def test_create_application_sets_open_status(monkeypatch):
    # Словарь для фиксации аргументов вызова DAO.create.
    called = {}

    async def fake_create(**kwargs):
        called.update(kwargs)

    # Подменяем получение user_id из cookies и запись в БД.
    monkeypatch.setattr(app_router, "get_user_id_from_cookies", lambda _: 11)
    monkeypatch.setattr(app_router.ApplicationsDAO, "create", fake_create)

    # Эмуляция form-объекта, который роут переводит в dict(...).
    class FormModel(dict):
        def __iter__(self):
            return iter({"title": "t", "description": "d"}.items())

    request = make_request(path="/applications/create")
    payload = FormModel(title="t", description="d")

    # Вызываем роут напрямую.
    response = asyncio.run(app_router.create_application(request, payload))

    # Проверяем редирект после успешного создания.
    assert response.status_code == 301
    # Проверяем, что user_id проставлен из cookies.
    assert called["user_id"] == 11
    # Проверяем, что статус новой заявки всегда is_open.
    assert called["status"] == ApplicationStatus.is_open


def test_get_application_404(monkeypatch):
    # Если заявка не найдена, роут должен вернуть 404.
    async def fake_get_one(**_):
        return None

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)

    request = make_request(path="/applications/99")
    request.state.user = {"id": 1}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(app_router.get_application(request, 99))

    assert exc.value.status_code == 404


def test_accept_application_updates_and_enqueues(monkeypatch):
    # Флаги, чтобы проверить оба побочных эффекта: update и enqueue email.
    called = {"updated": False, "queued": False}

    async def fake_get_one(**_):
        class UserObj:
            email = "u@test.local"

        # Возвращаем минимальный набор данных, нужный роуту.
        return {"id": 10, "title": "Заявка", "user": UserObj()}

    async def fake_update_one(_id, **kwargs):
        called["updated"] = True
        # Проверяем перевод статуса в in_process.
        assert kwargs["status"] == ApplicationStatus.in_process
        # Проверяем фиксацию исполнителя.
        assert kwargs["performer_id"] == 5

    def fake_enqueue(**kwargs):
        called["queued"] = True
        # Проверяем, что письмо ставится с правильным статусом.
        assert kwargs["status"] == ApplicationStatus.in_process

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)
    monkeypatch.setattr(app_router.ApplicationsDAO, "update_one", fake_update_one)
    monkeypatch.setattr(app_router, "get_user_id_from_token", lambda _: 5)
    monkeypatch.setattr(app_router, "enqueue_application_status_email", fake_enqueue)

    request = make_request(path="/applications/10/accept")
    request.state.user = {"full_name": "Исполнитель"}

    response = asyncio.run(app_router.accept_application(request, 10))

    assert response.status_code == 302
    assert called["updated"] is True
    assert called["queued"] is True


def test_close_application_forbidden_if_not_performer(monkeypatch):
    # Если закрывает не исполнитель, ожидаем 403 Forbidden.
    async def fake_get_one(**_):
        class UserObj:
            email = "u@test.local"

        return {"id": 10, "title": "Заявка", "user": UserObj(), "performer_id": 8}

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)
    monkeypatch.setattr(app_router, "get_user_id_from_token", lambda _: 5)

    request = make_request(path="/applications/10/close")
    request.state.user = {"full_name": "Исполнитель"}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(app_router.close_application(request, 10))

    assert exc.value.status_code == 403
