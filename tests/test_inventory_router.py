import asyncio

import pytest
from fastapi import HTTPException

from app.inventory.models import ToolStatus
from app.inventory import router as inv_router
from tests.conftest import make_request


def test_equip_inventory_item_updates_status(monkeypatch):
    # Подмена update_one для проверки, какой статус записывается в БД.
    async def fake_update_one(_id, **kwargs):
        assert kwargs["status"] == ToolStatus.used

    monkeypatch.setattr(inv_router.DAOTool, "update_one", fake_update_one)
    response = asyncio.run(inv_router.equip_inventory_item("INV-1"))

    # После успешного действия должен быть редирект в список инвентаря.
    assert response.status_code == 302
    # Проверяем установку anti-cache заголовков.
    assert response.headers["cache-control"].startswith("no-cache")


def test_put_inventory_item_updates_status(monkeypatch):
    # Аналогично проверяем возврат инструмента "на склад".
    async def fake_update_one(_id, **kwargs):
        assert kwargs["status"] == ToolStatus.in_storage

    monkeypatch.setattr(inv_router.DAOTool, "update_one", fake_update_one)
    response = asyncio.run(inv_router.put_inventory_item("INV-1"))

    assert response.status_code == 302


def test_create_inventory_raises_when_cabinet_not_found(monkeypatch):
    # DAO кабинетов возвращает False -> кабинет не существует.
    async def fake_check(**_):
        return False

    monkeypatch.setattr(inv_router.DAOCabinet, "check", fake_check)

    # Минимальная модель payload, поддерживающая доступ к атрибутам и dict(...).
    class Payload:
        inventory_number = "INV-1"
        name = "Ноутбук"
        status = ToolStatus.in_storage
        cabinet_name = "404"

        def __iter__(self):
            return iter({
                "inventory_number": self.inventory_number,
                "name": self.name,
                "status": self.status,
                "cabinet_name": self.cabinet_name,
            }.items())

    request = make_request(path="/inventory/create")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(inv_router.create_inventory(request, Payload()))

    # Ожидаем код 401 по текущей бизнес-логике роута.
    assert exc.value.status_code == 401


def test_get_inventory_item_404(monkeypatch):
    # Если DAO не нашел объект, роут должен отдать 404.
    async def fake_get_one(**_):
        return None

    monkeypatch.setattr(inv_router.DAOTool, "get_one", fake_get_one)
    request = make_request(path="/inventory/item/INV-404")
    request.state.user = {"id": 1}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(inv_router.get_inventory_item(request, "INV-404"))

    assert exc.value.status_code == 404
