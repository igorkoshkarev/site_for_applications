from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.users.router import router as user_router
from app.applications.router import router as application_router
from app.inventory.router import router as inventory_router
from app.middlewares import CheckLoginMiddleware, GetUserDataMiddleware


main = FastAPI()

main.add_middleware(CheckLoginMiddleware)
main.add_middleware(GetUserDataMiddleware)

main.mount('/static', StaticFiles(directory='app/static'), 'static')
templates = Jinja2Templates(directory=str('app/templates'))

@main.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

main.include_router(user_router)
main.include_router(application_router)
main.include_router(inventory_router)
