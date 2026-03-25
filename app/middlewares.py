from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response, RedirectResponse
from fastapi.requests import Request
from app.users.auth import get_user_token, get_user_id_from_token
from app.users.dao import DAOUser
import re


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
            user = await DAOUser.get_one(id=user_id)
        request.state.user = user

        response = await call_next(request)

        return response


class BaseRoleCheckMiddleware(BaseHTTPMiddleware):

    role_law = None
    pages = None

    async def dispatch(self, request: Request, call_next):
        user = request.state.user
        if self.check_page(request.url.path) and getattr(user['role'], self.role_law):
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
