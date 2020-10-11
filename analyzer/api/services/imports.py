from typing import List

from aiomisc import chunk_list
from asyncpgsa import PG

from analyzer.db.schema import imports_table, citizens_table, relations_table
from analyzer.utils.consts import MAX_QUERY_ARGS

MAX_CITIZENS_PER_INSERT = MAX_QUERY_ARGS // len(citizens_table.columns)
MAX_RELATIONS_PER_INSERT = MAX_QUERY_ARGS // len(relations_table.columns)


def make_citizen_rows(import_id: int, citizens: List[dict]):
    for citizen in citizens:
        yield {
            'import_id': import_id,
            'citizen_id': citizen['citizen_id'],
            'name': citizen['name'],
            'birth_date': citizen['birth_date'],
            'gender': citizen['gender'],
            'town': citizen['town'],
            'street': citizen['street'],
            'building': citizen['building'],
            'apartment': citizen['apartment']
        }


def make_relation_rows(import_id: int, citizens: List[dict]):
    for citizen in citizens:
        for relative_id in citizen['relatives']:
            yield {
                'import_id': import_id,
                'citizen_id': citizen['citizen_id'],
                'relative_id': relative_id
            }


async def create_import(db: PG, citizens: List[dict]) -> int:
    async with db.transaction() as conn:
        query = imports_table.insert().returning(imports_table.c.import_id)
        import_id = await conn.fetchval(query=query)

        citizen_rows = make_citizen_rows(import_id=import_id, citizens=citizens)
        relation_rows = make_relation_rows(import_id=import_id, citizens=citizens)

        chunked_citizen_rows = chunk_list(iterable=citizen_rows, size=MAX_CITIZENS_PER_INSERT)
        chunked_relation_rows = chunk_list(iterable=relation_rows, size=MAX_RELATIONS_PER_INSERT)

        query = citizens_table.insert()
        for chunk in chunked_citizen_rows:
            await conn.execute(query.values(list(chunk)))

        query = relations_table.insert()
        for chunk in chunked_relation_rows:
            await conn.execute(query.values(list(chunk)))

        return import_id
