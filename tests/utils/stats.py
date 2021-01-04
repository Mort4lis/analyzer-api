import math
import time
from copy import copy
from datetime import datetime, date, timedelta
from enum import Enum
from http import HTTPStatus
from itertools import groupby
from typing import List, Union

import numpy as np
import pytz
from aiohttp.test_utils import TestClient
from dateutil.relativedelta import relativedelta

from analyzer.api.schema import DATE_FORMAT
from analyzer.api.schema import (
    TownAgeStatResponseSchema,
)
from analyzer.api.views.stats import TownAgeStatView
from tests.utils.base import url_for

CURRENT_DATE = datetime(year=2021, month=1, day=4, tzinfo=pytz.utc)


def age2date(years: int, days: int = 0, base_date: date = CURRENT_DATE) -> str:
    """
    Возвращает дату рождения в виде строки для жителя, возраст которого составляет
    years лет и days дней. Дата рассчитывается исходя из базовой даты base_date.
    """
    birth_date = copy(base_date).replace(year=base_date.year - years)
    birth_date -= timedelta(days=days)
    return birth_date.strftime(DATE_FORMAT)


def date2age(birth_date: str, base_date: date = CURRENT_DATE) -> int:
    """
    Возвращает количество полных лет со дня рождения birth_date.

    Дата рассчитывается исходя из базовой даты base_date.
    [0:6] означает, что мы получаем (year, month, day, hour, minute, second) у даты.
    """
    birth_date = datetime(*(time.strptime(birth_date, DATE_FORMAT)[0:6]), tzinfo=pytz.utc)
    return relativedelta(base_date, birth_date).years


def round_half_up(n: Union[float, int], decimals: int = 0) -> float:
    """
    Арифметическое округление до значимых чисел decimals.
    """
    multiplier = 10 ** decimals
    return math.floor(n * multiplier + 0.5) / multiplier


def make_expected_age_stats(citizens: List[dict]) -> List[dict]:
    """
    Формирует корректный ожидамый вывод перцентилей возврастов, сгруппированных по городам.

    :param citizens: список жителей
    """
    town_ages = {}
    grouped_citizens = groupby(citizens, lambda citizen: citizen['town'])
    for town, citizens in grouped_citizens:
        town_ages[town] = [date2age(citizen['birth_date']) for citizen in citizens]

    response = []
    percentiles = (50, 75, 99)
    for town, ages in town_ages.items():
        response_item = {'town': town}
        for per in percentiles:
            response_item['p' + str(per)] = round_half_up(np.percentile(ages, per), decimals=2)
        response.append(response_item)
    return response


def compare_age_stats(left: List[dict], right: List[dict]) -> bool:
    """Сравнивает два вывода перцентилей возврастов, сгруппированных по городам."""
    left.sort(key=lambda item: item['town'])
    right.sort(key=lambda item: item['town'])

    return left == right


async def get_town_age_statistics(
        client: TestClient,
        import_id: int,
        expected_status: Union[int, Enum] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.get(
        url_for(TownAgeStatView.URL_PATH, import_id=import_id),
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = TownAgeStatResponseSchema().validate(data)
        assert errors == {}

        return data['data']
