from typing import List

from asyncpg import Record
from asyncpgsa import PG
from sqlalchemy import select, func, text

from analyzer.db.schema import citizens_table
from analyzer.utils.db import rounded

CURRENT_DATE = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")


async def get_town_age_statistics(db: PG, import_id: int) -> List[Record]:
    """
    Возвращает статистику возврастов жителей по городам.

    :param db: объект для взаимодействия с БД
    :param import_id: идентификатор выгрузки
    :return: статистика
    """
    age = func.age(CURRENT_DATE, citizens_table.c.birth_date)
    age = func.date_part("year", age)

    query = (
        select(
            [
                citizens_table.c.town,
                rounded(func.percentile_cont(0.5).within_group(age)).label("p50"),
                rounded(func.percentile_cont(0.75).within_group(age)).label("p75"),
                rounded(func.percentile_cont(0.99).within_group(age)).label("p99"),
            ]
        )
        .select_from(citizens_table)
        .group_by(citizens_table.c.town)
        .where(citizens_table.c.import_id == import_id)
    )

    stats = await db.fetch(query)
    return stats
