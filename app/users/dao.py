from app.users.models import Role, User
from app.dao import BaseDAO


class DAORole(BaseDAO):
    model = Role


class DAOUser(BaseDAO):
    model = User
