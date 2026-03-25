import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.applications.dao import ApplicationsDAO
from app.applications.models import ApplicationStatus
from app.applications.rb import ApplicationSearchFilter, CreateApplicationRB
from app.mail import enqueue_application_status_email
from app.schemas import PaginationModel
from app.users.auth import get_user_id_from_token
from app.utils import get_user_id_from_cookies


router = APIRouter(prefix="/applications", tags=["Applications"])
templates = Jinja2Templates(directory=str("app/templates"))
logger = logging.getLogger(__name__)


@router.get("/", summary="Get all applications")
async def get_applications(
    request: Request,
    filter: Annotated[ApplicationSearchFilter, Depends()],
    pagination: Annotated[PaginationModel, Depends()],
):
    applications = await ApplicationsDAO.get_all_with_limit(
        pagination.limit,
        pagination.get_offset(),
        **dict(filter),
    )
    return templates.TemplateResponse("applications.html", {
        "request": request,
        "user": request.state.user,
        "applications": applications,
        "filter": filter,
        "pagination": pagination.get_context(len(applications)),
    })


@router.get("/create", summary="Create application page")
async def create_application_page(request: Request):
    return templates.TemplateResponse("create_application.html", {
        "request": request,
        "user": request.state.user,
    })


@router.post("/create", summary="Create application")
async def create_application(request: Request, application_info: Annotated[CreateApplicationRB, Form()]):
    user_id = get_user_id_from_cookies(request)
    await ApplicationsDAO.create(user_id=user_id, **dict(application_info))
    return RedirectResponse("/applications", status_code=301)


@router.get("/{application_id}", summary="Get application")
async def get_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Page not found")

    return templates.TemplateResponse("application.html", {
        "request": request,
        "user": request.state.user,
        "application": application,
        "ApplicationStatus": ApplicationStatus,
    })


@router.get("/{application_id}/accept", summary="Accept application")
async def accept_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Page not found")

    performer_id = get_user_id_from_token(request)
    await ApplicationsDAO.update_one(
        application_id,
        status=ApplicationStatus.in_process,
        performer_id=performer_id,
    )

    enqueue_application_status_email(
        email=application["user"].email,
        status=ApplicationStatus.in_process,
        application_id=application["id"],
        title=application["title"],
        performer_name=request.state.user["full_name"],
    )

    return RedirectResponse(f"/applications/{application_id}", status_code=302)


@router.get("/{application_id}/close", summary="Close application")
async def close_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Page not found")
    if application["performer_id"] != get_user_id_from_token(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    await ApplicationsDAO.update_one(application_id, status=ApplicationStatus.is_closed)

    enqueue_application_status_email(
        email=application["user"].email,
        status=ApplicationStatus.is_closed,
        application_id=application["id"],
        title=application["title"],
        performer_name=request.state.user["full_name"],
    )

    return RedirectResponse(f"/applications/{application_id}", status_code=302)
