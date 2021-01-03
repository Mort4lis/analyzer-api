from datetime import date, timedelta
from enum import Enum
from http import HTTPStatus
from typing import List, Union

import pytest
from aiohttp.test_utils import TestClient

from analyzer.api.schema import DATE_FORMAT
from analyzer.utils.consts import MAX_INTEGER, LONGEST_STR
from tests.utils.citizens import generate_citizen, generate_citizens, compare_citizen_groups, fetch_citizens_request
from tests.utils.imports import create_import_request

CASES = (
    # Житель без родственников.
    # Обработчик должен корректно создавать выгрузку с одним жителем.
    (
        [
            generate_citizen(relatives=[]),
        ],
        HTTPStatus.CREATED
    ),

    # Житель с несколькими родственниками.
    # Обработчик должен корректно добавлять жителей и создавать
    # родственные связи.
    (
        [
            generate_citizen(citizen_id=1, relatives=[2, 3]),
            generate_citizen(citizen_id=2, relatives=[1]),
            generate_citizen(citizen_id=3, relatives=[1]),
        ],
        HTTPStatus.CREATED
    ),

    # Житель сам себе родственник.
    # Обработчик должен позволять создавать такие родственные связи.
    (
        [
            generate_citizen(citizen_id=1, relatives=[1]),
        ],
        HTTPStatus.CREATED
    ),

    # Выгрузка с максимально длинными/большими значениями.
    # aiohttp должен разрешать запросы такого размера, а обработчик не должен
    # на них падать.
    (
        generate_citizens(
            citizens_count=10000,
            relations_count=1000,
            start_citizen_id=MAX_INTEGER - 10000,
            name=LONGEST_STR,
            town=LONGEST_STR,
            street=LONGEST_STR,
            building=LONGEST_STR,
            apartment=MAX_INTEGER,
        ),
        HTTPStatus.CREATED
    ),

    # Пустая выгрузка
    # Обработчик не должен падать на таких данных.
    (
        [],
        HTTPStatus.CREATED
    ),

    # Дата рождения - текущая дата
    (
        [
            generate_citizen(
                birth_date=date.today().strftime(DATE_FORMAT)
            )
        ],
        HTTPStatus.CREATED
    ),

    # Дата рождения некорректная (в будущем)
    (
        [
            generate_citizen(
                birth_date=(date.today() + timedelta(days=1)).strftime(DATE_FORMAT)
            )
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # citizen_id не уникален в рамках выгрузки
    (
        [
            generate_citizen(citizen_id=1),
            generate_citizen(citizen_id=1),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Родственная связь указана неверно (нет обратной)
    (
        [
            generate_citizen(citizen_id=1, relatives=[2]),
            generate_citizen(citizen_id=2, relatives=[]),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Родственная связь c несуществующим жителем
    (
        [
            generate_citizen(citizen_id=1, relatives=[3]),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Родственные связи не уникальны
    (
        [
            generate_citizen(citizen_id=1, relatives=[2]),
            generate_citizen(citizen_id=2, relatives=[1, 1]),
        ],
        HTTPStatus.BAD_REQUEST
    ),
)


@pytest.mark.parametrize(['citizens', 'expected_status'], CASES)
async def test_create_import(
        api_client: TestClient,
        citizens: List[dict],
        expected_status: Union[int, Enum]
) -> None:
    import_id = await create_import_request(
        client=api_client,
        citizens=citizens,
        expected_status=expected_status,
    )

    if expected_status == HTTPStatus.CREATED:
        received_citizens = await fetch_citizens_request(
            client=api_client,
            import_id=import_id,
        )
        assert compare_citizen_groups(left=received_citizens, right=citizens)
