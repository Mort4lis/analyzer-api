from datetime import date, timedelta
from http import HTTPStatus

import pytest
from aiohttp.test_utils import TestClient
from asyncpgsa import PG

from analyzer.api.schema import DATE_FORMAT
from analyzer.db.schema import Gender
from tests.utils.citizens import (
    generate_citizen,
    generate_citizens,
    compare_citizen_groups,
    compare_citizens,
    fetch_citizens_request,
    patch_citizen_request,
)
from tests.utils.imports import create_import_db, create_import_request


async def test_patch_citizen(api_client: TestClient):
    """
    Проверяет, что данные о жителе и его родственниках успешно обновляются.
    """
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # тремя жителями, чтобы убедиться, что обработчик различает жителей
    # разных выгрузок и изменения не затронут жителей другой выгрузки.

    side_citizens = [
        generate_citizen(citizen_id=1),
        generate_citizen(citizen_id=2),
        generate_citizen(citizen_id=3),
    ]
    side_import_id = await create_import_request(
        client=api_client,
        citizens=side_citizens
    )

    # Создаем выгрузку с тремя жителями, два из которых родственники для
    # тестирования изменений.
    citizens = [
        generate_citizen(citizen_id=1, relatives=[2]),
        generate_citizen(citizen_id=2, relatives=[1]),
        generate_citizen(citizen_id=3, relatives=[])
    ]
    import_id = await create_import_request(
        client=api_client,
        citizens=citizens
    )

    # Обновляем часть полей о жителе, чтобы убедиться что PATCH позволяет
    # передавать только некоторые поля.
    # Данные меняем сразу в выгрузке, чтобы потом было легче сравнивать.
    citizens[0]['name'] = 'Иванова Иванна Ивановна'
    updated_citizen = await patch_citizen_request(
        client=api_client,
        import_id=import_id,
        citizen_id=citizens[0]['citizen_id'],
        data={'name': citizens[0]['name']}
    )
    assert compare_citizens(left=citizens[0], right=updated_citizen)

    # Обновляем другую часть данных, чтобы проверить что данные обновляются.
    citizens[0]['gender'] = Gender.female.value
    citizens[0]['birth_date'] = '02.02.2002'
    citizens[0]['town'] = 'Другой город'
    citizens[0]['street'] = 'Другая улица'
    citizens[0]['building'] = 'Другое строение'
    citizens[0]['apartment'] += 1
    # У жителя #1 одна родственная связь должна исчезнуть (с жителем #2),
    # и одна появиться (с жителем #3).
    citizens[0]['relatives'] = [citizens[2]['citizen_id']]
    # Родственные связи должны быть двусторонними:
    # - у жителя #3 родственная связь с жителем #1 добавляется.
    # - у жителя #2 родственная связь с жителем #1 удаляется
    citizens[2]['relatives'].append(citizens[0]['citizen_id'])
    citizens[1]['relatives'].remove(citizens[0]['citizen_id'])

    updated_citizen = await patch_citizen_request(
        client=api_client,
        import_id=import_id,
        citizen_id=citizens[0]['citizen_id'],
        data={
            field: citizens[0][field] for field in [
                'gender', 'birth_date',
                'town', 'street', 'building',
                'apartment', 'relatives'
            ]
        }
    )
    assert compare_citizens(left=citizens[0], right=updated_citizen)

    # Проверяем всю выгрузку, чтобы убедиться что родственные связи всех
    # жителей изменились корректно.
    received_citizens = await fetch_citizens_request(
        client=api_client,
        import_id=import_id
    )
    assert compare_citizen_groups(left=citizens, right=received_citizens)

    # Проверяем, что изменение жителя в тестируемой выгрузке не испортило
    # данные в дополнительной выгрузке.
    received_citizens = await fetch_citizens_request(
        client=api_client,
        import_id=side_import_id
    )
    assert compare_citizen_groups(left=side_citizens, right=received_citizens)


async def test_patch_self_relative_citizen(api_client: TestClient, migrated_postgres_conn: PG) -> None:
    """Проверяем что жителю можно указать себя родственником."""
    citizen = generate_citizen(citizen_id=1, relatives=[])
    citizens = [citizen]
    import_id = await create_import_db(dataset=citizens, conn=migrated_postgres_conn)

    citizen['relatives'] = [citizen['citizen_id']]
    updated_citizen = await patch_citizen_request(
        client=api_client,
        import_id=import_id,
        citizen_id=citizen['citizen_id'],
        data={k: v for k, v in citizen.items() if k != 'citizen_id'}
    )
    assert compare_citizens(left=citizen, right=updated_citizen)


invalid_cases = [
    # Сервис должен запрещать устанавливать дату рождения в будущем.
    {
        'birth_date': (date.today() + timedelta(days=1)).strftime(DATE_FORMAT)
    },

    # Сервис должен запрещать добавлять жителю несуществующего родственника.
    {
        'relatives': [999]
    }
]


@pytest.mark.parametrize('data', invalid_cases)
async def test_invalid_patch_citizen(api_client: TestClient, migrated_postgres_conn: PG, data: dict) -> None:
    citizens = generate_citizens(citizens_count=1)
    import_id = await create_import_db(dataset=citizens, conn=migrated_postgres_conn)

    await patch_citizen_request(
        client=api_client,
        import_id=import_id,
        citizen_id=citizens[0]['citizen_id'],
        data=data,
        expected_status=HTTPStatus.BAD_REQUEST
    )


async def test_patch_nonexistent_citizen(api_client: TestClient, migrated_postgres_conn: PG) -> None:
    """Сервис должен возвращать корректный статус при обновлении несуществующих сущностей."""
    # Обновляем жителя в несуществующей выгрузке
    await patch_citizen_request(
        client=api_client,
        import_id=999,
        citizen_id=999,
        data={'name': 'Ivan Ivanov'},
        expected_status=HTTPStatus.NOT_FOUND
    )

    # Обновляем несуществующего жителя в существующем импорте
    import_id = await create_import_db(
        dataset=[],
        conn=migrated_postgres_conn
    )
    await patch_citizen_request(
        client=api_client,
        import_id=import_id,
        citizen_id=999,
        data={'name': 'Ivan Ivanov'},
        expected_status=HTTPStatus.NOT_FOUND
    )
