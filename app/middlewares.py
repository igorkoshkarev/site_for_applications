from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response, RedirectResponse
from fastapi.requests import Request
from app.users.auth import get_user_token


class CheckLoginMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        deny_redirect = [request.url_for('login_page'), request.url_for('registration_page')]

        if not get_user_token(request) and request.url not in deny_redirect:
            return RedirectResponse('/users/login', status_code=302)
        
        response = await call_next(request)

        return response
