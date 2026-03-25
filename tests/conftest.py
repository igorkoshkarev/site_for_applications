from starlette.requests import Request


def make_request(path: str = "/", method: str = "GET", cookies: dict | None = None):
    # Формируем минимальный ASGI scope, достаточный для создания тестового Request.
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    # Создаем объект запроса так же, как это делает Starlette/FastAPI.
    request = Request(scope)
    # Подставляем cookies вручную, чтобы тестировать авторизацию и middleware.
    request._cookies = cookies or {}
    return request
