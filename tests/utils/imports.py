from datetime import datetime
from enum import Enum
from http import HTTPStatus
from typing import List, Union

from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from analyzer.api.schema import ImportResponseSchema, DATE_FORMAT
from analyzer.api.views.imports import ImportView
from analyzer.db.schema import imports_table, citizens_table, relations_table
from tests.utils.base import url_for


async def create_import_db(dataset: List[dict], conn: PG) -> int:
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


async def create_import_request(
        client: TestClient,
        citizens: list,
        expected_status: Union[int, Enum] = HTTPStatus.CREATED,
        **request_kwargs
) -> int:
    response = await client.post(
        url_for(ImportView.URL_PATH),
        json={'citizens': citizens},
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.CREATED:
        data = await response.json()
        errors = ImportResponseSchema().validate(data)
        assert errors == {}

        return data['data']['import_id']
