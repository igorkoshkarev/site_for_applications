from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
main = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))


@main.get("/", response_class=HTMLResponse)
def main_page(request: Request):
    print(request)
    return templates.TemplateResponse('index.html', {"request": request})



