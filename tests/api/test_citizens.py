from datetime import datetime
from http import HTTPStatus
from typing import List

import pytest
from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from analyzer.api.schema import CitizenListResponseSchema, DATE_FORMAT
from analyzer.api.views.citizens import CitizenListView
from analyzer.db.schema import imports_table, citizens_table, relations_table
from tests.utils.base import url_for
from tests.utils.citizens import generate_citizen, compare_citizen_groups

datasets = [
    # Житель с несколькими родственниками.
    # Обработчик должен корректно возвращать жителя со всеми родственниками.
    [
        generate_citizen(citizen_id=1, relatives=[2, 3]),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[1])
    ],

    # Житель без родственников.
    # Поле relatives должно содержать пустой список (может иметь значение [None]),
    # которое появляется при агрегации строк с LEFT JOIN.
    #
    [
        generate_citizen(relatives=[])
    ],

    # Житель, который сам себе родственник.
    # Обработчик должен возвращать индектификатор жителя в списке родственников.
    [
        generate_citizen(citizen_id=1, relatives=[1])
    ],

    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    [],
]


async def create_import(dataset: List[dict], conn: PG) -> int:
    query = imports_table.insert().returning(imports_table.c.import_id)
    import_id = await conn.fetchval(query)

    citizen_rows = []
    relative_rows = []

    for item in dataset:
        citizen = {
            **item,
            'import_id': import_id,
            'birth_date': datetime.strptime(item['birth_date'], DATE_FORMAT).date()
        }
        relatives = citizen.pop('relatives')
        citizen_rows.append(citizen)

        for relative_id in relatives:
            relative_rows.append({
                'import_id': import_id,
                'citizen_id': citizen['citizen_id'],
                'relative_id': relative_id
            })

    if citizen_rows:
        query = citizens_table.insert().values(citizen_rows)
        await conn.execute(query)

    if relative_rows:
        query = relations_table.insert().values(relative_rows)
        await conn.execute(query)

    return import_id


@pytest.mark.parametrize('dataset', datasets)
async def test_get_citizens(api_client: TestClient, migrated_postgres_conn: PG, dataset: List[dict]) -> None:
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с одним жителем,
    # чтобы убедиться, что обработчик различает жителей из разных выгрузок.
    await create_import(dataset=[generate_citizen()], conn=migrated_postgres_conn)

    import_id = await create_import(dataset=dataset, conn=migrated_postgres_conn)
    response = await api_client.get(
        path=url_for(
            path=CitizenListView.URL_PATH,
            import_id=import_id,
        )
    )
    assert response.status == HTTPStatus.OK

    data = await response.json()
    errors = CitizenListResponseSchema().validate(data)
    assert errors == {}

    citizens = data['data']
    assert compare_citizen_groups(left=citizens, right=dataset)
