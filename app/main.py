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


@main.middleware("http")
async def force_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self' data:; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'",
    )
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@main.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse('index.html', {
        "request": request,
        "user": request.state.user
        })

main.include_router(user_router)
main.include_router(application_router)
main.include_router(inventory_router)
