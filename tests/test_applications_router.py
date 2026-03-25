import asyncio

import pytest
from fastapi import HTTPException

from app.applications.models import ApplicationStatus
from app.applications import router as app_router
from tests.conftest import make_request


def test_create_application_sets_open_status(monkeypatch):
    called = {}

    async def fake_create(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(app_router, "get_user_id_from_cookies", lambda _: 11)
    monkeypatch.setattr(app_router, "verify_csrf_token", lambda *_: True)
    monkeypatch.setattr(app_router.ApplicationsDAO, "create", fake_create)

    class FormModel(dict):
        def __iter__(self):
            return iter({"title": "t", "description": "d"}.items())

    request = make_request(path="/applications/create")
    payload = FormModel(title="t", description="d")

    response = asyncio.run(app_router.create_application(request, payload, "csrf-ok"))

    assert response.status_code == 301
    assert called["user_id"] == 11
    assert called["status"] == ApplicationStatus.is_open


def test_get_application_404(monkeypatch):
    async def fake_get_one(**_):
        return None

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)

    request = make_request(path="/applications/99")
    request.state.user = {"id": 1}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(app_router.get_application(request, 99))

    assert exc.value.status_code == 404


def test_accept_application_updates_and_enqueues(monkeypatch):
    called = {"updated": False, "queued": False}

    async def fake_get_one(**_):
        class UserObj:
            email = "u@test.local"

        return {"id": 10, "title": "Заявка", "user": UserObj()}

    async def fake_update_one(_id, **kwargs):
        called["updated"] = True
        assert kwargs["status"] == ApplicationStatus.in_process
        assert kwargs["performer_id"] == 5

    def fake_enqueue(**kwargs):
        called["queued"] = True
        assert kwargs["status"] == ApplicationStatus.in_process

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)
    monkeypatch.setattr(app_router.ApplicationsDAO, "update_one", fake_update_one)
    monkeypatch.setattr(app_router, "verify_csrf_token", lambda *_: True)
    monkeypatch.setattr(app_router, "get_user_id_from_token", lambda _: 5)
    monkeypatch.setattr(app_router, "enqueue_application_status_email", fake_enqueue)

    request = make_request(path="/applications/10/accept")
    request.state.user = {"full_name": "Исполнитель"}

    response = asyncio.run(app_router.accept_application(request, 10, "csrf-ok"))

    assert response.status_code == 302
    assert called["updated"] is True
    assert called["queued"] is True


def test_close_application_forbidden_if_not_performer(monkeypatch):
    async def fake_get_one(**_):
        class UserObj:
            email = "u@test.local"

        return {"id": 10, "title": "Заявка", "user": UserObj(), "performer_id": 8}

    monkeypatch.setattr(app_router.ApplicationsDAO, "get_one", fake_get_one)
    monkeypatch.setattr(app_router, "verify_csrf_token", lambda *_: True)
    monkeypatch.setattr(app_router, "get_user_id_from_token", lambda _: 5)

    request = make_request(path="/applications/10/close")
    request.state.user = {"full_name": "Исполнитель"}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(app_router.close_application(request, 10, "csrf-ok"))

    assert exc.value.status_code == 403
