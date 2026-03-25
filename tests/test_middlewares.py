import asyncio

from starlette.responses import Response

from app.middlewares import CheckLoginMiddleware, GetUserDataMiddleware
from tests.conftest import make_request


def test_check_login_redirects_to_login_without_token():
    # Инициализируем middleware с заглушкой ASGI-приложения.
    middleware = CheckLoginMiddleware(app=lambda scope, receive, send: None)
    # Создаем защищенный URL без токена в cookies.
    request = make_request(path="/applications")

    async def call_next(_):
        # Если middleware пропустит запрос, вернем обычный 200-ответ.
        return Response("ok", status_code=200)

    # Запускаем async dispatch в синхронном тесте.
    response = asyncio.run(middleware.dispatch(request, call_next))
    # Ожидаем редирект на страницу логина.
    assert response.status_code == 302
    assert response.headers["location"] == "/users/login"


def test_check_login_allows_static_without_token():
    # Проверяем исключение для статики: она должна открываться без авторизации.
    middleware = CheckLoginMiddleware(app=lambda scope, receive, send: None)
    request = make_request(path="/static/site.css")

    async def call_next(_):
        return Response("ok", status_code=200)

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200


def test_get_user_data_sets_state_user(monkeypatch):
    # Middleware должен прочитать user_id из токена и положить пользователя в request.state.
    middleware = GetUserDataMiddleware(app=lambda scope, receive, send: None)
    request = make_request(path="/")

    # Подменяем извлечение ID пользователя из токена.
    monkeypatch.setattr("app.middlewares.get_user_id_from_token", lambda _: 3)

    async def fake_get_one(**kwargs):
        # Проверяем, что в DAO передается ожидаемый фильтр.
        assert kwargs == {"id": 3}
        return {"id": 3, "username": "ivanov"}

    monkeypatch.setattr("app.middlewares.DAOUser.get_one", fake_get_one)

    async def call_next(req):
        # Здесь уже должен быть проставлен state.user.
        assert req.state.user["id"] == 3
        return Response("ok", status_code=200)

    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
