from passlib.context import CryptContext
import datetime
from datetime import timezone, timedelta
from app.config import get_auth_data
from jose import jwt


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