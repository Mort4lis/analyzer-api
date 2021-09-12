from typing import List

import pytest
from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from tests.utils.citizens import (
    generate_citizen,
    compare_citizen_groups,
    fetch_citizens_request,
)
from tests.utils.imports import create_import_db

datasets = [
    # Житель с несколькими родственниками.
    # Обработчик должен корректно возвращать жителя со всеми родственниками.
    [
        generate_citizen(citizen_id=1, relatives=[2, 3]),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[1]),
    ],
    # Житель без родственников.
    # Поле relatives должно содержать пустой список (может иметь значение [None]),
    # которое появляется при агрегации строк с LEFT JOIN.
    #
    [generate_citizen(relatives=[])],
    # Житель, который сам себе родственник.
    # Обработчик должен возвращать индектификатор жителя в списке родственников.
    [generate_citizen(citizen_id=1, relatives=[1])],
    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    [],
]


@pytest.mark.parametrize("dataset", datasets)
async def test_get_citizens(api_client: TestClient, migrated_postgres_conn: PG, dataset: List[dict]) -> None:
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с одним жителем,
    # чтобы убедиться, что обработчик различает жителей из разных выгрузок.
    await create_import_db(dataset=[generate_citizen()], conn=migrated_postgres_conn)

    import_id = await create_import_db(dataset=dataset, conn=migrated_postgres_conn)
    citizens = await fetch_citizens_request(
        client=api_client,
        import_id=import_id,
    )
    assert compare_citizen_groups(left=citizens, right=dataset)
