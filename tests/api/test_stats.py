from http import HTTPStatus
from typing import List
from unittest.mock import patch

import pytest
from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from tests.utils.citizens import (
    generate_citizen,
)
from tests.utils.imports import create_import_db
from tests.utils.stats import (
    get_town_age_statistics,
    age2date,
    make_expected_age_stats,
    compare_age_stats,
    CURRENT_DATE
)

datasets = [
    # Несколько жителей у которых завтра день рождения.
    # Проверяется что обработчик использует в рассчетах количество полных лет.
    [
        generate_citizen(citizen_id=1, birth_date=age2date(years=10, days=364), town='Москва'),
        generate_citizen(citizen_id=2, birth_date=age2date(years=30, days=364), town='Москва'),
        generate_citizen(citizen_id=3, birth_date=age2date(years=50, days=364), town='Москва'),
    ],

    # Житель у которого сегодня день рождения.
    # Проверяет краевой случай, возраст жителя у которого сегодня день рождения
    # не должен рассчитаться как на 1 год меньше.
    [
        generate_citizen(birth_date=age2date(years=10), town='Псков')
    ],

    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    []
]


@pytest.mark.parametrize('citizens', datasets)
@patch('analyzer.api.services.stats.CURRENT_DATE', new=CURRENT_DATE)
async def test_get_town_age_statistics(
        api_client: TestClient,
        migrated_postgres_conn: PG,
        citizens: List[dict]
) -> None:
    # Перед прогоном каждого теста добавим в БД дополнительную выгрузку с
    # жителем из другого города, чтобы убедиться, что обработчик различает
    # жителей разных выгрузок.
    await create_import_db(
        dataset=[generate_citizen(town='Псков')],
        conn=migrated_postgres_conn
    )

    import_id = await create_import_db(
        dataset=citizens,
        conn=migrated_postgres_conn
    )

    stats = await get_town_age_statistics(client=api_client, import_id=import_id)
    expected_stats = make_expected_age_stats(citizens)
    assert compare_age_stats(left=stats, right=expected_stats)


async def test_get_nonexistence_import_town_age_stats(api_client: TestClient) -> None:
    await get_town_age_statistics(
        client=api_client,
        import_id=999,
        expected_status=HTTPStatus.NOT_FOUND
    )
