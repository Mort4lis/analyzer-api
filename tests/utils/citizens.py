from enum import Enum
from http import HTTPStatus
from random import randint, choice, shuffle
from typing import List, Mapping, Iterable, Union

import faker
from aiohttp.test_utils import TestClient

from analyzer.api.schema import CitizenListResponseSchema, DATE_FORMAT
from analyzer.api.views.citizens import CitizenListView
from analyzer.utils.consts import MAX_INTEGER
from tests.utils.base import url_for

fake = faker.Faker('ru_RU')


def generate_citizen(
        citizen_id: int = None,
        name: str = None,
        birth_date: str = None,
        gender: str = None,
        town: str = None,
        street: str = None,
        building: str = None,
        apartment: int = None,
        relatives: List[int] = None
) -> dict:
    """Создает и возвращает жителя, автоматически генерируя данные для неуказанных полей."""
    citizen_id = citizen_id or randint(0, MAX_INTEGER)
    gender = gender or choice(('female', 'male'))
    name = name or (fake.name_female() if gender == 'female' else fake.name_male())
    birth_date = birth_date or fake.date_of_birth(
        minimum_age=0, maximum_age=80
    ).strftime(DATE_FORMAT)
    town = town or fake.city_name()
    street = street or fake.street_name()
    building = building or str(randint(1, 100))
    apartment = apartment or randint(1, 120)
    relatives = relatives or []

    return {
        'citizen_id': citizen_id,
        'name': name,
        'birth_date': birth_date,
        'gender': gender,
        'town': town,
        'street': street,
        'building': building,
        'apartment': apartment,
        'relatives': relatives,
    }


def generate_citizens(
        citizens_count: int,
        relations_count: int,
        start_citizen_id: int = 0,
        **citizen_kwargs: dict
) -> List[dict]:
    """
    Генерирует список жителей.

    :param citizens_count: количество жителей, которое будет сгенерированно
    :param relations_count: количество родственных связей, которое будет сгенерированно
    :param start_citizen_id: с какого id начинать
    :param citizen_kwargs: ключевые аргументы для функции generate_citizens
    :raise ValueError: если не может проставить родственную связь для жителя
    :return: список сгенерированных жителей со связями
    """
    citizens = {}
    max_citizen_id = start_citizen_id + citizens_count - 1

    for citizen_id in range(start_citizen_id, max_citizen_id + 1):
        citizens[citizen_id] = generate_citizen(citizen_id=citizen_id, **citizen_kwargs)

    unassigned_relatives = relations_count or citizens_count // 10
    shuffled_citizen_ids = list(citizens.keys())

    while unassigned_relatives:
        shuffle(shuffled_citizen_ids)

        citizen_id = shuffled_citizen_ids[0]
        for relative_id in shuffled_citizen_ids[1:]:
            if relative_id not in citizens[citizen_id]['relatives']:
                citizens[citizen_id]['relatives'].append(relative_id)
                citizens[relative_id]['relatives'].append(citizen_id)
                break
        else:
            raise ValueError('Unable to choose relative for citizen')

        unassigned_relatives -= 1

    return list(citizens.values())


def normalize_citizen(citizen: Mapping) -> dict:
    """Нормализует жителя для сравнения с другим."""
    return {**citizen, 'relatives': sorted(citizen['relatives'])}


def compare_citizens(left: Mapping, right: Mapping) -> bool:
    """Сравнивает двух жителей, перед этим нормализуя их."""
    return normalize_citizen(left) == normalize_citizen(right)


def compare_citizen_groups(left: Iterable, right: Iterable) -> bool:
    """Сравнивает два списка групп."""
    left = [normalize_citizen(citizen) for citizen in left]
    left.sort(key=lambda citizen: citizen['citizen_id'])

    right = [normalize_citizen(citizen) for citizen in right]
    right.sort(key=lambda citizen: citizen['citizen_id'])

    return left == right


async def fetch_citizens_request(
        client: TestClient,
        import_id: int,
        expected_status: Union[int, Enum] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.get(
        url_for(CitizenListView.URL_PATH, import_id=import_id),
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = CitizenListResponseSchema().validate(data)
        assert errors == {}

        return data['data']
