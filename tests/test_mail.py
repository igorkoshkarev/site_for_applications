import asyncio
from fastapi_mail import MessageSchema

from app.applications.models import ApplicationStatus
from app import mail


def test_build_message_for_in_process():
    # Проверяем генерацию темы/текста письма для статуса "в работе".
    subject, body = mail._build_message(ApplicationStatus.in_process, 5, "Принтер", "Иванов")
    assert "accepted" in subject
    assert "Иванов" in body


def test_build_message_for_closed():
    # Проверяем генерацию письма для статуса "закрыта".
    subject, body = mail._build_message(ApplicationStatus.is_closed, 7, "Сеть")
    assert "completed" in subject
    assert "has been completed" in body


def test_enqueue_ignored_without_email(monkeypatch):
    # Флаг, чтобы увидеть, вызывался ли asyncio.create_task.
    called = {"create_task": False}

    def fake_create_task(coro):
        # Если функция вызвалась, фиксируем это и закрываем coroutine,
        # чтобы не получить предупреждение "never awaited".
        called["create_task"] = True
        coro.close()

    # Подменяем create_task и сбрасываем очередь.
    monkeypatch.setattr(asyncio, "create_task", fake_create_task)
    mail._mail_queue = None

    # Без email задача отправки вообще не должна создаваться.
    mail.enqueue_application_status_email(
        email=None,
        status=ApplicationStatus.in_process,
        application_id=1,
        title="t",
    )

    assert called["create_task"] is False


def test_enqueue_fallback_creates_task(monkeypatch):
    # Проверяем fallback-поведение: если очередь не инициализирована,
    # создается ad-hoc task через asyncio.create_task.
    called = {"create_task": False}

    def fake_create_task(coro):
        called["create_task"] = True
        coro.close()

    monkeypatch.setattr(asyncio, "create_task", fake_create_task)
    mail._mail_queue = None

    mail.enqueue_application_status_email(
        email="a@b.c",
        status=ApplicationStatus.in_process,
        application_id=2,
        title="title",
    )

    assert called["create_task"] is True


def test_send_email_skips_when_not_configured(monkeypatch):
    # Проверяем, что при отсутствующей SMTP-конфигурации функция
    # завершается без исключений и без попытки реальной отправки.
    async def run():
        monkeypatch.setattr(mail, "_is_mail_configured", lambda: False)
        await mail.send_application_status_email(
            email="a@b.c",
            status=ApplicationStatus.in_process,
            application_id=1,
            title="title",
        )

    asyncio.run(run())


def test_send_email_calls_fastmail(monkeypatch):
    # Сохраняем факт вызова и тему письма для проверок.
    sent = {"called": False, "subject": ""}

    class FakeFastMail:
        # Подставной клиент FastMail вместо реального SMTP.
        def __init__(self, _):
            pass

        async def send_message(self, message: MessageSchema):
            sent["called"] = True
            sent["subject"] = message.subject

    async def run():
        # Эмулируем наличие SMTP-настроек.
        monkeypatch.setattr(mail, "_is_mail_configured", lambda: True)
        # Подменяем FastMail и конфиг, чтобы тест не ходил в сеть.
        monkeypatch.setattr(mail, "FastMail", FakeFastMail)
        monkeypatch.setattr(mail, "_get_mail_config", lambda: object())

        await mail.send_application_status_email(
            email="a@b.c",
            status=ApplicationStatus.in_process,
            application_id=3,
            title="title",
            performer_name="Петров",
        )

    asyncio.run(run())
    assert sent["called"] is True
    assert "accepted" in sent["subject"]
