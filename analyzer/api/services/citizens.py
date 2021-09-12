from itertools import groupby
from typing import Iterable, Dict

from aiohttp.web import HTTPNotFound
from asyncpg import ForeignKeyViolationError
from asyncpgsa import PG
from asyncpgsa.connection import SAConnection
from marshmallow import ValidationError
from sqlalchemy import select, and_, func, or_, cast, Integer

from analyzer.db.schema import citizens_table, relations_table
from analyzer.utils.db import AsyncPGCursor

CITIZENS_QUERY = (
    select(
        [
            citizens_table.c.citizen_id,
            citizens_table.c.name,
            citizens_table.c.birth_date,
            citizens_table.c.gender,
            citizens_table.c.town,
            citizens_table.c.street,
            citizens_table.c.building,
            citizens_table.c.apartment,
            func.array_remove(func.array_agg(relations_table.c.relative_id), None).label("relatives"),
        ]
    )
    .select_from(
        citizens_table.outerjoin(
            relations_table,
            and_(
                citizens_table.c.import_id == relations_table.c.import_id,
                citizens_table.c.citizen_id == relations_table.c.citizen_id,
            ),
        )
    )
    .group_by(citizens_table.c.import_id, citizens_table.c.citizen_id)
)


async def acquire_lock(conn: SAConnection, import_id: int) -> None:
    """
    Рекомендательная блокировка.

    https://postgrespro.ru/docs/postgrespro/10/explicit-locking#ADVISORY-LOCKS

    :param conn: объект соединения
    :param import_id: идентификатор выгрузки
    """
    await conn.execute("SELECT pg_advisory_xact_lock($1)", import_id)


def get_citizens_cursor(db: PG, import_id: int) -> AsyncPGCursor:
    """
    Возвращает курсор для асинхронного получения данных о жителях по определенной выгрузке.

    :param db: объект для взаимодействия с БД
    :param import_id: идентфикатор выгрузки
    :return: объект курсора
    """
    query = CITIZENS_QUERY.where(citizens_table.c.import_id == import_id)
    return AsyncPGCursor(query=query, transaction_ctx=db.transaction())


async def get_citizen(conn: SAConnection, import_id: int, citizen_id: int) -> dict:
    """
    Возвращает жителя по идентификатору жителя в указанной выгрузке.

    :param conn: объект соединения
    :param import_id: идентификатор выгрузки
    :param citizen_id: идентфикатор жителя
    :return: словарь с данными жителя
    """
    query = CITIZENS_QUERY.where(
        and_(
            citizens_table.c.import_id == import_id,
            citizens_table.c.citizen_id == citizen_id,
        )
    )
    return await conn.fetchrow(query)


async def add_relatives(conn: SAConnection, import_id: int, citizen_id: int, relatives: Iterable[int]) -> None:
    """
    Добавляет записи в таблицу родственных связей (relation_table).

    :param conn: объект соединения
    :param import_id: идентификатор выгрузки
    :param citizen_id: идентфикатор жителя
    :param relatives: идентификаторы родственников для добавления
    :raise ValidationError
    """
    values = []
    for relative_id in relatives:
        values.append(
            {
                "import_id": import_id,
                "citizen_id": citizen_id,
                "relative_id": relative_id,
            }
        )

        if citizen_id != relative_id:
            values.append(
                {
                    "import_id": import_id,
                    "citizen_id": relative_id,
                    "relative_id": citizen_id,
                }
            )

    query = relations_table.insert().values(values)

    try:
        await conn.execute(query)
    except ForeignKeyViolationError:
        raise ValidationError(
            message="Unable to add relatives {0}, some do not exist".format(relatives),
            field_name="relatives",
        )


async def remove_relatives(conn: SAConnection, import_id: int, citizen_id: int, relatives: Iterable[int]) -> None:
    """
    Удаляет записи из таблицы родственных связей (relation_table).

    :param conn: объект соединения
    :param import_id: идентификатор выгрузки
    :param citizen_id: идентфикатор жителя
    :param relatives: идентификаторы родственников для удаления
    """
    conditions = []

    for relative_id in relatives:
        conditions.extend(
            [
                and_(
                    relations_table.c.import_id == import_id,
                    relations_table.c.citizen_id == citizen_id,
                    relations_table.c.relative_id == relative_id,
                ),
                and_(
                    relations_table.c.import_id == import_id,
                    relations_table.c.citizen_id == relative_id,
                    relations_table.c.relative_id == citizen_id,
                ),
            ]
        )

    query = relations_table.delete().where(or_(*conditions))
    await conn.execute(query)


async def update_citizen(conn: SAConnection, import_id: int, citizen: dict, updated_data: dict) -> dict:
    """
    Обновляет жителя по идентификатору жителя в указанной выгрузке.

    :param conn: объект соединения
    :param import_id: идентификатор выгрузки
    :param citizen: текущие данные жителя
    :param updated_data: данные для обновления
    """
    citizen_kwargs = {
        "conn": conn,
        "import_id": import_id,
        "citizen_id": citizen["citizen_id"],
    }
    updated_citizen_data = {field: value for field, value in updated_data.items() if field != "relatives"}
    if updated_citizen_data:
        query = (
            citizens_table.update()
            .values(updated_citizen_data)
            .where(
                and_(
                    citizens_table.c.import_id == import_id,
                    citizens_table.c.citizen_id == citizen["citizen_id"],
                )
            )
        )
        await conn.execute(query)

    if "relatives" in updated_data:
        current_relatives = set(citizen["relatives"])  # {1}
        updated_relatives = set(updated_data["relatives"])  # {2}

        relatives_for_add = updated_relatives - current_relatives  # нужно ли добавить родственные связи
        relatives_for_remove = current_relatives - updated_relatives  # нужно ли удалить родственные связи

        if relatives_for_add:
            await add_relatives(**citizen_kwargs, relatives=relatives_for_add)
        if relatives_for_remove:
            await remove_relatives(**citizen_kwargs, relatives=relatives_for_remove)

    return await get_citizen(**citizen_kwargs)


async def partially_update_citizen(db: PG, import_id: int, citizen_id: int, updated_data: dict) -> dict:
    """
    Частичное обновление жителя.

    :param db: объект для взаимодействия с БД
    :param import_id: идентификатор выгрузки
    :param citizen_id: идентификатор жителя
    :param updated_data: актуальные данные для обновления жителя
    :return: обновленное состояние жителя
    """
    async with db.transaction() as conn:
        # Блокировка позволит избежать состояние гонки между конкурентными
        # запросами на изменение родственников
        await acquire_lock(conn=conn, import_id=import_id)

        citizen = await get_citizen(conn=conn, import_id=import_id, citizen_id=citizen_id)

        if not citizen:
            raise HTTPNotFound

        return await update_citizen(conn=conn, import_id=import_id, citizen=citizen, updated_data=updated_data)


async def get_citizen_birthdays_by_months(db: PG, import_id: int) -> Dict[int, list]:
    """
    Возвращает жителей и количество подарков, которые они будут покупать
    своим близжашим родственникам, сгруппированных по месяцам.

    :param db: объект для взаимодействия с БД
    :param import_id: идентификатор выгрузки
    :return: статистику по месяцам
    """
    month = func.date_part("month", citizens_table.c.birth_date)
    month = cast(month, Integer).label("month")
    query = (
        select(
            [
                month,
                relations_table.c.citizen_id,
                func.count(relations_table.c.relative_id).label("presents"),
            ]
        )
        .select_from(
            relations_table.outerjoin(
                citizens_table,
                and_(
                    relations_table.c.import_id == citizens_table.c.import_id,
                    relations_table.c.relative_id == citizens_table.c.citizen_id,
                ),
            )
        )
        .group_by(month, relations_table.c.import_id, relations_table.c.citizen_id)
        .where(relations_table.c.import_id == import_id)
    )
    rows = await db.fetch(query)

    result = {str(i): [] for i in range(1, 13)}
    for month, rows in groupby(rows, key=lambda row: row["month"]):
        for row in rows:
            result[str(month)].append({"citizen_id": row["citizen_id"], "presents": row["presents"]})

    return result
