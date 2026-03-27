import asyncio

import pytest
from fastapi import HTTPException

from app.inventory.models import ToolStatus
from app.inventory import router as inv_router
from tests.conftest import make_request


def test_equip_inventory_item_updates_status(monkeypatch):
    async def fake_update_one(_id, **kwargs):
        assert kwargs["status"] == ToolStatus.used

    monkeypatch.setattr(inv_router.DAOTool, "update_one", fake_update_one)
    monkeypatch.setattr(inv_router, "verify_csrf_token", lambda *_: True)
    request = make_request(path="/inventory/item/INV-1/equip")
    response = asyncio.run(inv_router.equip_inventory_item(request, "INV-1", "csrf-ok"))

    assert response.status_code == 302
    assert response.headers["cache-control"].startswith("no-cache")


def test_put_inventory_item_updates_status(monkeypatch):
    async def fake_update_one(_id, **kwargs):
        assert kwargs["status"] == ToolStatus.in_storage

    monkeypatch.setattr(inv_router.DAOTool, "update_one", fake_update_one)
    monkeypatch.setattr(inv_router, "verify_csrf_token", lambda *_: True)
    request = make_request(path="/inventory/item/INV-1/put")
    response = asyncio.run(inv_router.put_inventory_item(request, "INV-1", "csrf-ok"))

    assert response.status_code == 302


def test_create_inventory_raises_when_cabinet_not_found(monkeypatch):
    async def fake_check(**_):
        return False

    monkeypatch.setattr(inv_router.DAOCabinet, "check", fake_check)
    monkeypatch.setattr(inv_router, "verify_csrf_token", lambda *_: True)

    request = make_request(path="/inventory/create")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            inv_router.create_inventory(
                request,
                "INV-1",
                "Ноутбук",
                ToolStatus.in_storage,
                "404",
                "csrf-ok",
            )
        )

    assert exc.value.status_code == 401


def test_get_inventory_item_404(monkeypatch):
    async def fake_get_one(**_):
        return None

    monkeypatch.setattr(inv_router.DAOTool, "get_one", fake_get_one)
    request = make_request(path="/inventory/item/INV-404")
    request.state.user = {"id": 1}

    with pytest.raises(HTTPException) as exc:
        asyncio.run(inv_router.get_inventory_item(request, "INV-404"))

    assert exc.value.status_code == 404
