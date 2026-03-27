from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from app.users.auth import get_user_token, get_user_id_from_token
from app.users.dao import DAOUser
from app.config import settings
import re


class CheckLoginMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        public_path_prefixes = (
            "/users/login",
            "/users/registration",
            "/static/",
            "/favicon.ico",
        )

        user_id = get_user_id_from_token(request)
        if not user_id and not request.url.path.startswith(public_path_prefixes):
            response = RedirectResponse('/users/login', status_code=302)
            response.delete_cookie(
                "users_access_token",
                secure=settings.COOKIE_SECURE,
                httponly=True,
                samesite=settings.COOKIE_SAMESITE,
            )
            response.delete_cookie(
                "csrf_token",
                secure=settings.COOKIE_SECURE,
                httponly=True,
                samesite=settings.COOKIE_SAMESITE,
            )
            return response
        
        response = await call_next(request)

        return response


class GetUserDataMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        user_id = get_user_id_from_token(request)
        user = None
        if user_id:
            user = await DAOUser.get_one(id=user_id)
        request.state.user = user

        response = await call_next(request)

        return response


class BaseRoleCheckMiddleware(BaseHTTPMiddleware):

    role_law = None
    pages = None

    async def dispatch(self, request: Request, call_next):
        user = request.state.user
        if self.check_page(request.url.path) and user and getattr(user['role'], self.role_law):
            response = await call_next(request)
        elif not self.check_page(request.url.path):
            response = await call_next(request)
        else:
            return RedirectResponse('/', status_code=302)
        return response
    
    def check_page(self, path):
        for page in self.pages:
            if re.match(page, path):
                return True
        return False


class ShowInventoryRoleCheckMiddleware(BaseRoleCheckMiddleware):

    role_law = 'law_show_inventory'
    pages = [r'\/inventory[.]*']


class AddInventoryRoleCheckMiddleware(BaseRoleCheckMiddleware):

    role_law = 'law_add_inventory'
    pages = [r'\/inventory\/create[\/]?']


class ChangeStatusInventoryRoleCheckMiddleware(BaseRoleCheckMiddleware):

    role_law = 'law_use_inventory'
    pages = [r'\/inventory\/item\/[^\/]+\/put[\/]?', r'\/inventory\/item\/[^\/]+\/equip[\/]?']


class ChangeStatusApplicationsRoleCheckMiddleware(BaseRoleCheckMiddleware):

    role_law = 'law_update_applications'
    pages = [r'\/applications\/[^\/]+\/accept[\/]?', r'\/applications\/[^\/]+\/close[\/]?']

class OpenAdminPanelRoleCheckMiddleware(BaseRoleCheckMiddleware):

    role_law = 'law_open_admin_panel'
    pages = [r'\/admin[.]*']


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
