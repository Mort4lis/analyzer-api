from typing import List, Dict

import pytest
from aiohttp.test_utils import TestClient
from asyncpgsa import PG
from http import HTTPStatus

from tests.utils.citizens import (
    generate_citizens,
    generate_citizen,
    get_citizen_birthdays,
)
from tests.utils.imports import create_import_db


def make_birthdays_response(values: Dict[str, list] = None) -> dict:
    """
    Генерирует словарь, в котором ключи - номера месяцев, а значения - списки
    жителей и подарков (по умолчению []).
    """
    response = {}
    values = values or {}
    for month in range(1, 13):
        month = str(month)
        response[month] = values.get(month, [])
    return response


datasets = [
    # Житель, у которого несколько родственников.
    # Обработчик должен корректно показывать сколько подарков приобретет
    # житель #1 своим родственникам в каждом месяце.
    (
        [
            generate_citizen(citizen_id=1, birth_date='31.12.2020', relatives=[2, 3]),
            generate_citizen(citizen_id=2, birth_date='11.02.2020', relatives=[1]),
            generate_citizen(citizen_id=3, birth_date='17.02.2020', relatives=[1]),
        ],
        make_birthdays_response({
            '2': [
                {'citizen_id': 1, 'presents': 2}
            ],
            '12': [
                {'citizen_id': 2, 'presents': 1},
                {'citizen_id': 3, 'presents': 1}
            ]
        })
    ),

    # Выгрузка с жителем, который сам себе родственник.
    # Обработчик должен корректно показывать что житель купит себе подарок в
    # месяц своего рождения.
    (
        [
            generate_citizen(citizen_id=1, birth_date='17.02.2020', relatives=[1])
        ],
        make_birthdays_response({
            '2': [
                {'citizen_id': 1, 'presents': 1}
            ]
        })
    ),

    # Житель без родственников.
    # Обработчик не должен учитывать его при расчетах.
    (
        [
            generate_citizen(relatives=[])
        ],
        make_birthdays_response()
    ),

    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    (
        [],
        make_birthdays_response()
    ),
]


@pytest.mark.parametrize(['citizens', 'expected_birthdays'], datasets)
async def test_citizen_birthdays(
        api_client: TestClient,
        migrated_postgres_conn: PG,
        citizens: List[dict],
        expected_birthdays: dict
) -> None:
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # двумя родственниками, чтобы убедиться, что обработчик различает жителей
    # разных выгрузок.
    await create_import_db(
        dataset=generate_citizens(citizens_count=3),
        conn=migrated_postgres_conn
    )

    import_id = await create_import_db(
        dataset=citizens,
        conn=migrated_postgres_conn
    )
    birthdays = await get_citizen_birthdays(
        client=api_client,
        import_id=import_id
    )

    assert expected_birthdays == birthdays


async def test_get_nonexistence_import_birthdays(api_client: TestClient) -> None:
    await get_citizen_birthdays(
        client=api_client,
        import_id=999,
        expected_status=HTTPStatus.NOT_FOUND
    )
