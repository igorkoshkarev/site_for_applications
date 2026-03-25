import asyncio

import pytest
from fastapi import HTTPException
from starlette.responses import Response

from app.users import router as users_router
from tests.conftest import make_request


def test_create_user_hashes_password_and_redirects(monkeypatch):
    # Сюда собираем аргументы вызова DAOUser.create.
    called = {}

    # Подменяем хэширование, чтобы предсказуемо проверить результат.
    monkeypatch.setattr(users_router, "get_password_hash", lambda p: f"hashed::{p}")

    async def fake_create(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(users_router.DAOUser, "create", fake_create)

    # Эмуляция объекта RBRegistration, который приходит из формы.
    class RB(dict):
        def __init__(self):
            self.username = "ivan"
            self.password = "Password1"
            self.verify_password = "Password1"
            self.full_name = "Ivan Ivanov"
            self.email = "ivan@test.local"
            self.phone = "+79001234567"
            self.cabinet = "101"

        def model_dump(self, exclude=None):
            data = {
                "username": self.username,
                "password": self.password,
                "verify_password": self.verify_password,
                "full_name": self.full_name,
                "email": self.email,
                "phone": self.phone,
                "cabinet": self.cabinet,
            }
            # Исключаем поля так же, как делает pydantic model_dump.
            if exclude:
                for key in exclude:
                    data.pop(key, None)
            return data

    request = make_request(path="/users/registration", method="POST")
    response = asyncio.run(users_router.create_user(request, RB()))

    # После регистрации роут редиректит на страницу логина.
    assert response.status_code == 302
    # Проверяем автоподстановку дефолтной роли.
    assert called["role_name"] == users_router.DAORole.DEFAULT_ROLE
    # Проверяем, что в DAO ушел уже хэшированный пароль.
    assert called["password"].startswith("hashed::")


def test_login_user_success_sets_cookie(monkeypatch):
    # Подменяем DAO и криптографию, чтобы сфокусироваться на логике роута.
    async def fake_check(**_):
        return True

    async def fake_get_one(**_):
        return {"id": 9, "password": "hashed"}

    monkeypatch.setattr(users_router.DAOUser, "check", fake_check)
    monkeypatch.setattr(users_router.DAOUser, "get_one", fake_get_one)
    monkeypatch.setattr(users_router, "verify_password", lambda p, h: True)
    monkeypatch.setattr(users_router, "create_access_token", lambda _: "token")

    class Login:
        username = "ivan"
        password = "Password1"

    response = asyncio.run(users_router.login_user(Response(), Login()))

    # Проверяем редирект в профиль пользователя.
    assert response.status_code == 301
    assert response.headers["location"] == "/users/9"
    # Проверяем, что роут выставил auth-cookie.
    assert "users_access_token=" in response.headers.get("set-cookie", "")


def test_login_user_invalid_credentials(monkeypatch):
    # DAO сообщает, что пользователь не найден -> ожидаем 401.
    async def fake_check(**_):
        return False

    monkeypatch.setattr(users_router.DAOUser, "check", fake_check)

    class Login:
        username = "ivan"
        password = "Password1"

    with pytest.raises(HTTPException) as exc:
        asyncio.run(users_router.login_user(Response(), Login()))

    assert exc.value.status_code == 401


def test_foreign_account_404(monkeypatch):
    # Профиль не найден в БД -> роут должен вернуть 404.
    async def fake_get_one(**_):
        return None

    monkeypatch.setattr(users_router.DAOUser, "get_one", fake_get_one)
    monkeypatch.setattr(users_router, "get_user_id_from_token", lambda _: 404)

    request = make_request(path="/users/404")
    request.state.user = {"id": 1}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(users_router.foreign_account(request, 404))

    assert exc.value.status_code == 404
