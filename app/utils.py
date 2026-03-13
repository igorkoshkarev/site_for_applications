from fastapi.requests import Request
from app.users.auth import decode_token


def get_user_id_from_cookies(request: Request):
    token = request.cookies.get('users_access_token')
    if token:
        decoded_token = decode_token(token)
        return int(decoded_token['sub'])
    raise ValueError('Данный куки не существует')