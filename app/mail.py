import logging
import asyncio

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.applications.models import ApplicationStatus
from app.config import settings


logger = logging.getLogger(__name__)
_mail_queue: asyncio.Queue[dict] | None = None
_mail_worker_task: asyncio.Task | None = None


def _is_mail_configured() -> bool:
    required = (
        settings.MAIL_SERVER,
        settings.MAIL_PORT,
        settings.MAIL_FROM,
        settings.MAIL_USERNAME,
        settings.MAIL_PASSWORD,
    )
    return all(required)


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


def _build_message(
    status: ApplicationStatus,
    application_id: int,
    title: str,
    performer_name: str | None = None,
) -> tuple[str, str]:
    if status == ApplicationStatus.in_process:
        subject = f"Application #{application_id} accepted"
        body = (
            f"Your application #{application_id} ({title}) is accepted and now in progress.\n"
            f"Assigned performer: {performer_name or 'assigned'}."
        )
    elif status == ApplicationStatus.is_closed:
        subject = f"Application #{application_id} completed"
        body = f"Your application #{application_id} ({title}) has been completed."
    else:
        subject = f"Application #{application_id} status changed"
        body = f"Application #{application_id} ({title}) status changed to: {status}."
    return subject, body


async def send_application_status_email(
    *,
    email: str | None,
    status: ApplicationStatus,
    application_id: int,
    title: str,
    performer_name: str | None = None,
) -> None:
    if not email:
        return
    if not _is_mail_configured():
        logger.warning(
            "SMTP settings are not configured. Email to %s for application %s was not sent.",
            email,
            application_id,
        )
        return

    subject, body = _build_message(status, application_id, title, performer_name)
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


async def send_application_feedback_email(
    *,
    email: str | None,
    application_id: int,
    title: str,
    feedback: str,
    applicant_name: str | None = None,
) -> None:
    if not email:
        return
    if not _is_mail_configured():
        logger.warning(
            "SMTP settings are not configured. Feedback email for application %s was not sent.",
            application_id,
        )
        return

    subject = f"Feedback for application #{application_id}"
    body = (
        f"Application #{application_id} ({title}) has a new feedback from applicant "
        f"{applicant_name or 'user'}.\n\n"
        f"Feedback text:\n{feedback}"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(_get_mail_config())
    await fm.send_message(message)


async def _mail_worker() -> None:
    if _mail_queue is None:
        return

    while True:
        payload = await _mail_queue.get()
        try:
            message_type = payload.pop("message_type", "status")
            if message_type == "feedback":
                await send_application_feedback_email(**payload)
            else:
                await send_application_status_email(**payload)
        except Exception as exc:
            logger.exception(
                "Failed to send email for application %s: %s",
                payload.get("application_id"),
                exc,
            )
        finally:
            _mail_queue.task_done()


def start_mail_worker() -> None:
    global _mail_queue, _mail_worker_task

    if _mail_worker_task and not _mail_worker_task.done():
        return

    _mail_queue = asyncio.Queue(maxsize=1000)
    _mail_worker_task = asyncio.create_task(_mail_worker())
    logger.info("Mail worker started")


async def stop_mail_worker() -> None:
    global _mail_queue, _mail_worker_task

    if _mail_worker_task:
        _mail_worker_task.cancel()
        try:
            await _mail_worker_task
        except asyncio.CancelledError:
            pass

    _mail_worker_task = None
    _mail_queue = None
    logger.info("Mail worker stopped")


def enqueue_application_status_email(
    *,
    email: str | None,
    status: ApplicationStatus,
    application_id: int,
    title: str,
    performer_name: str | None = None,
) -> None:
    if not email:
        return

    payload = {
        "email": email,
        "status": status,
        "application_id": application_id,
        "title": title,
        "performer_name": performer_name,
    }

    if _mail_queue is None:
        logger.warning("Mail queue is not initialized, fallback to ad-hoc task")
        asyncio.create_task(send_application_status_email(**payload))
        return

    try:
        _mail_queue.put_nowait({"message_type": "status", **payload})
    except asyncio.QueueFull:
        logger.error("Mail queue is full. Dropping email for application %s", application_id)


def enqueue_application_feedback_email(
    *,
    email: str | None,
    application_id: int,
    title: str,
    feedback: str,
    applicant_name: str | None = None,
) -> None:
    if not email:
        return

    payload = {
        "email": email,
        "application_id": application_id,
        "title": title,
        "feedback": feedback,
        "applicant_name": applicant_name,
    }

    if _mail_queue is None:
        logger.warning("Mail queue is not initialized, fallback to ad-hoc task")
        asyncio.create_task(send_application_feedback_email(**payload))
        return

    try:
        _mail_queue.put_nowait({"message_type": "feedback", **payload})
    except asyncio.QueueFull:
        logger.error("Mail queue is full. Dropping feedback email for application %s", application_id)
