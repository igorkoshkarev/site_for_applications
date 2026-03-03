from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


main = FastAPI()
main.mount('/static', StaticFiles(directory='app/static'), 'static')
templates = Jinja2Templates(directory=str('app/templates'))



@main.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})



