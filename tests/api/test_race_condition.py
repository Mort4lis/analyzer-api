import asyncio

from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from tests.utils.citizens import (
    generate_citizens,
    fetch_citizens_request,
    patch_citizen_request,
)
from tests.utils.imports import create_import_db


async def test_race_condition(api_client: TestClient, migrated_postgres_conn: PG) -> None:
    """
    При обновлении жителя между разными запросами может произойти гонка, в
    результате которой БД может прийти в неконсистентное состояние.

    Например: есть некий житель без родственников, с citizen_id=1. Выполняется два
    конкурентных запроса: первый добавляет жителю #1 родственника #2, второй
    добавляет жителю #1 родственника #3.

    Ожидается, что запросы должны выполниться последовательно, что в результате у
    жителя останется набор родственников из последнего выполненного запроса.

    В случае, если присутствует эффект состояния гонки, у жителя #1
    окажется два родственника (#2, #3).
    """
    # Создаем трех жителей, без родственников с citizen_id #1, #2 и #3.
    citizens = generate_citizens(citizens_count=3, start_citizen_id=1)
    import_id = await create_import_db(
        dataset=citizens,
        conn=migrated_postgres_conn
    )

    # Житель, которому мы будем добавлять родственников
    citizen_id = citizens[0]['citizen_id']

    # Мы хотим отправить два конкурентных запроса с добавлением новой
    # родственной связи
    datasets = [
        {'relatives': [citizens[1]['citizen_id']]},
        {'relatives': [citizens[2]['citizen_id']]},
    ]

    await asyncio.gather(*[
        patch_citizen_request(
            client=api_client,
            import_id=import_id,
            citizen_id=citizen_id,
            data=dataset
        ) for dataset in datasets
    ])

    # Проверяем кол-во родственников у изменяемого жителя
    # (должно быть равно 1).
    received_citizens = {
        citizen['citizen_id']: citizen
        for citizen in await fetch_citizens_request(
            client=api_client,
            import_id=import_id
        )
    }
    assert len(received_citizens[citizen_id]['relatives']) == 1
