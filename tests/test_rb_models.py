import pytest
from pydantic import ValidationError

from app.applications.rb import CreateApplicationRB
from app.inventory.models import ToolStatus
from app.inventory.rb import CreateInventoryRB
from app.users.rb import RBRegistration


def test_registration_valid_model():
    # Проверяем успешную валидацию корректной регистрационной формы.
    data = RBRegistration(
        username="ivanov",
        full_name="Ivan Ivanov",
        email="ivan@example.com",
        phone="+79001234567",
        cabinet="101",
        password="Password1",
        verify_password="Password1",
    )
    assert data.username == "ivanov"


def test_registration_invalid_phone():
    # Передаем заведомо неверный формат телефона и ожидаем ошибку валидации.
    with pytest.raises(ValidationError):
        RBRegistration(
            username="ivanov",
            full_name="Ivan Ivanov",
            email="ivan@example.com",
            phone="abc",
            cabinet="101",
            password="Password1",
            verify_password="Password1",
        )


def test_registration_password_mismatch():
    # Проверяем model_validator: password и verify_password должны совпадать.
    with pytest.raises(ValidationError):
        RBRegistration(
            username="ivanov",
            full_name="Ivan Ivanov",
            email="ivan@example.com",
            phone="+79001234567",
            cabinet="101",
            password="Password1",
            verify_password="Password2",
        )


def test_create_application_rb_constraints():
    # Валидный объект заявки должен создаваться без ошибок.
    model = CreateApplicationRB(title="Принтер", description="Не печатает")
    assert model.title == "Принтер"

    # Пустой title нарушает ограничение min_length=1.
    with pytest.raises(ValidationError):
        CreateApplicationRB(title="", description="x")


def test_create_inventory_rb_defaults():
    # Если статус не передан, должен примениться дефолт in_storage.
    model = CreateInventoryRB(inventory_number="INV-1", name="Ноутбук", cabinet_name="101")
    assert model.status == ToolStatus.in_storage
