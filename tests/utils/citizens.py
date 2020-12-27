from random import randint, choice
from typing import List

import faker

MAX_INTEGER = 2147483647

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
    )
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
