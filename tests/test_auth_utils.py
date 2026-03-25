import pytest

from app.users.auth import create_access_token, decode_token, get_password_hash, verify_password
from app.utils import get_user_id_from_cookies


def test_password_hash_and_verify():
    # Исходный пароль, который будет захэширован.
    plain = "SecurePass123"
    # Генерируем хэш пароля через passlib.
    hashed = get_password_hash(plain)

    # Хэш не должен совпадать с исходной строкой.
    assert hashed != plain
    # Оригинальный пароль должен успешно проходить проверку.
    assert verify_password(plain, hashed) is True
    # Неверный пароль должен отвергаться.
    assert verify_password("WrongPass123", hashed) is False


def test_token_create_and_decode_contains_subject():
    # Создаем JWT с субъектом пользователя.
    token = create_access_token({"sub": "42"})
    # Раскодируем токен и читаем payload.
    payload = decode_token(token)

    # Проверяем, что поле sub сохранилось корректно.
    assert payload["sub"] == "42"
    # Проверяем, что в токене есть срок жизни (exp).
    assert "exp" in payload


def test_get_user_id_from_cookies_success(monkeypatch):
    # Минимальный объект запроса с cookie токена.
    class Req:
        cookies = {"users_access_token": "token"}

    # Подменяем decode_token, чтобы не зависеть от реального JWT.
    monkeypatch.setattr("app.utils.decode_token", lambda _: {"sub": "7"})

    # Функция должна вернуть ID из токена как int.
    assert get_user_id_from_cookies(Req()) == 7


def test_get_user_id_from_cookies_raises_when_no_cookie():
    # Кейс отсутствия cookie с токеном.
    class Req:
        cookies = {}

    # Ожидаем ValueError из util-функции.
    with pytest.raises(ValueError):
        get_user_id_from_cookies(Req())
