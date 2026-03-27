import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.applications.dao import ApplicationsDAO
from app.applications.models import ApplicationStatus
from app.applications.rb import ApplicationFeedbackRB, ApplicationSearchFilter, CreateApplicationRB
from app.mail import enqueue_application_feedback_email, enqueue_application_status_email
from app.schemas import PaginationModel
from app.users.auth import get_user_id_from_token, verify_csrf_token
from app.utils import get_user_id_from_cookies


router = APIRouter(prefix="/applications", tags=["Applications"])
templates = Jinja2Templates(directory=str("app/templates"))
logger = logging.getLogger(__name__)


def _normalize_status(value: object) -> str:
    if hasattr(value, "name"):
        return str(getattr(value, "name"))
    raw = str(value)
    if "." in raw:
        raw = raw.split(".")[-1]
    mapping = {"1": "is_open", "2": "in_process", "3": "is_closed", "4": "is_confirmed"}
    return mapping.get(raw, raw)


def _can_view_all_applications(user: dict | None) -> bool:
    if not user:
        return False
    role = user.get("role")
    return bool(role and getattr(role, "law_update_applications", False))


@router.get("/", summary="Get all applications")
async def get_applications(
    request: Request,
    filter: Annotated[ApplicationSearchFilter, Depends()],
    pagination: Annotated[PaginationModel, Depends()],
):
    current_user_id = get_user_id_from_token(request)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    filter_data = dict(filter)
    if not _can_view_all_applications(request.state.user):
        filter_data["user_id"] = current_user_id

    applications = await ApplicationsDAO.get_all_with_limit(
        pagination.limit,
        pagination.get_offset(),
        **filter_data,
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
async def create_application(
    request: Request,
    title: Annotated[str, Form(min_length=1, max_length=140)],
    description: Annotated[str, Form(max_length=1000)],
    csrf_token: Annotated[str, Form()],
):
    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    user_id = get_user_id_from_cookies(request)
    application_info = CreateApplicationRB(title=title, description=description)
    await ApplicationsDAO.create(
        user_id=user_id,
        status=ApplicationStatus.is_open,
        **dict(application_info),
    )
    return RedirectResponse("/applications", status_code=301)


@router.get("/{application_id}", summary="Get application")
async def get_application(request: Request, application_id: int):
    application = await ApplicationsDAO.get_one(id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Page not found")

    current_user_id = get_user_id_from_token(request)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if (
        not _can_view_all_applications(request.state.user)
        and application["user_id"] != current_user_id
        and application.get("performer_id") != current_user_id
    ):
        raise HTTPException(status_code=403, detail="Forbidden")

    can_leave_feedback = (
        _normalize_status(application["status"]) == "is_closed"
        and application["user_id"] == current_user_id
    )

    return templates.TemplateResponse("application.html", {
        "request": request,
        "user": request.state.user,
        "application": application,
        "ApplicationStatus": ApplicationStatus,
        "can_leave_feedback": can_leave_feedback,
        "feedback_sent": request.query_params.get("feedback") == "sent",
    })


@router.post("/{application_id}/accept", summary="Accept application")
async def accept_application(request: Request, application_id: int, csrf_token: Annotated[str, Form()]):
    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

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


@router.post("/{application_id}/close", summary="Close application")
async def close_application(request: Request, application_id: int, csrf_token: Annotated[str, Form()]):
    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

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


@router.post("/{application_id}/feedback", summary="Send feedback to performer")
async def send_feedback(
    request: Request,
    application_id: int,
    feedback: Annotated[str, Form(min_length=3, max_length=2000)],
    csrf_token: Annotated[str, Form()],
):
    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    application = await ApplicationsDAO.get_one(id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Page not found")

    current_user_id = get_user_id_from_token(request)
    if application["user_id"] != current_user_id:
        raise HTTPException(status_code=403, detail="Only applicant can send feedback")

    if _normalize_status(application["status"]) != "is_closed":
        raise HTTPException(status_code=400, detail="Feedback is available only for completed applications")

    performer = application.get("performer")
    if not performer or not performer.email:
        raise HTTPException(status_code=400, detail="Performer email is not configured")

    applicant_name = request.state.user["full_name"] if request.state.user else None
    feedback_info = ApplicationFeedbackRB(feedback=feedback)
    enqueue_application_feedback_email(
        email=performer.email,
        application_id=application["id"],
        title=application["title"],
        feedback=feedback_info.feedback,
        applicant_name=applicant_name,
    )

    return RedirectResponse(f"/applications/{application_id}?feedback=sent", status_code=302)
