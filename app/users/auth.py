from passlib.context import CryptContext
import datetime
import secrets
import hmac
from datetime import timezone, timedelta
from app.config import get_auth_data
from jose import jwt
from fastapi.requests import Request


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt


def decode_token(token: str) -> dict:
    auth_data = get_auth_data()
    decoded_jwt = jwt.decode(token, key=auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    return decoded_jwt


def get_user_token(request: Request):
    return request.cookies.get('users_access_token')


def get_user_id_from_token(request: Request):
    token = get_user_token(request)
    if token:
        try:
            return int(decode_token(token)['sub'])
        except Exception:
            return None
    return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf_token(request: Request, form_token: str | None) -> bool:
    cookie_token = request.cookies.get("csrf_token")
    return bool(cookie_token and form_token and hmac.compare_digest(cookie_token, form_token))
