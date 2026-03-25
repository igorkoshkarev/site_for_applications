import pytest

from app.schemas import PaginationModel


def test_pagination_context_and_offset():
    # Создаем объект пагинации: по 10 элементов на странице, текущая страница №2.
    page = PaginationModel(limit=10, page=2)

    # Строим контекст пагинации для общего числа элементов = 35.
    context = page.get_context(total=35)

    # Проверяем расчет общего числа страниц: 35/10 = 4 страницы.
    assert context["pages"] == 4
    # Проверяем корректный расчет следующей страницы.
    assert context["next_page"] == 3
    # Проверяем корректный расчет предыдущей страницы.
    assert context["prev_page"] == 1
    # Проверяем смещение (offset) для SQL-запроса: (2-1)*10 = 10.
    assert page.get_offset() == 10


def test_pagination_zero_total():
    # Кейс, когда в таблице нет записей.
    page = PaginationModel(limit=10, page=1)
    context = page.get_context(total=0)

    # При нуле записей число страниц должно быть 0.
    assert context["pages"] == 0
    # next/prev остаются на текущей странице.
    assert context["next_page"] == 1
    assert context["prev_page"] == 1


def test_pagination_validation_error():
    # Проверяем, что валидация pydantic срабатывает на невалидных параметрах.
    with pytest.raises(Exception):
        PaginationModel(limit=-1, page=0)
