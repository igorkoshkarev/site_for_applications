from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response, RedirectResponse
from fastapi.requests import Request
from app.users.auth import get_user_token, get_user_id_from_token
from app.users.dao import DAOUser


class CheckLoginMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        deny_redirect = [request.url_for('login_page'), request.url_for('registration_page')]

        if not get_user_token(request) and request.url not in deny_redirect:
            return RedirectResponse('/users/login', status_code=302)
        
        response = await call_next(request)

        return response


class GetUserDataMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        user_id = get_user_id_from_token(request)
        user = None
        if user_id:
            user = DAOUser.get_one(id=user_id)
        request.state.user = user
        
        response = await call_next(request)

        return response
