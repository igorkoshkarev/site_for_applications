from app.dao import BaseDAO
from app.applications.models import Application


class ApplicationsDAO(BaseDAO):
    model = Application
