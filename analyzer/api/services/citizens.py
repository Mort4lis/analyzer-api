from asyncpgsa import PG
from sqlalchemy import select, and_, func

from analyzer.db.schema import citizens_table, relations_table
from analyzer.utils.db import AsyncPGCursor

CITIZENS_QUERY = select([
    citizens_table.c.citizen_id,
    citizens_table.c.name,
    citizens_table.c.birth_date,
    citizens_table.c.gender,
    citizens_table.c.town,
    citizens_table.c.street,
    citizens_table.c.building,
    citizens_table.c.apartment,
    func.array_remove(
        func.array_agg(relations_table.c.relative_id),
        None
    ).label('relatives')
]).select_from(
    citizens_table.outerjoin(
        relations_table,
        and_(
            citizens_table.c.import_id == relations_table.c.import_id,
            citizens_table.c.citizen_id == relations_table.c.citizen_id
        )
    )
).group_by(
    citizens_table.c.import_id,
    citizens_table.c.citizen_id
)


def get_citizens_cursor(db: PG, import_id: int) -> AsyncPGCursor:
    query = CITIZENS_QUERY.where(
        citizens_table.c.import_id == import_id
    )
    return AsyncPGCursor(
        query=query,
        transaction_ctx=db.transaction()
    )
