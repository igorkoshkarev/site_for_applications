from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.users.router import router as user_router
from app.applications.router import router as application_router
from app.inventory.router import router as inventory_router
import app.middlewares as middleware
from app.admin import admin, lifespan


main = FastAPI(lifespan=lifespan)
main.add_middleware(middleware.OpenAdminPanelRoleCheckMiddleware)
main.add_middleware(middleware.ChangeStatusApplicationsRoleCheckMiddleware)
main.add_middleware(middleware.ChangeStatusInventoryRoleCheckMiddleware)
main.add_middleware(middleware.AddInventoryRoleCheckMiddleware)
main.add_middleware(middleware.ShowInventoryRoleCheckMiddleware)
main.add_middleware(middleware.CheckLoginMiddleware)
main.add_middleware(middleware.GetUserDataMiddleware)
main.add_middleware(middleware.SecurityHeadersMiddleware)


main.mount('/static', StaticFiles(directory='app/static'), 'static')
main.mount('/admin', admin.app)
templates = Jinja2Templates(directory=str('app/templates'))

@main.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse('index.html', {
        "request": request,
        "user": request.state.user
        })

main.include_router(user_router)
main.include_router(application_router)
main.include_router(inventory_router)
