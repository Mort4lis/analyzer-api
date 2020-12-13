from asyncpg import Connection
from aiohttp.test_utils import TestClient


async def test_get_citizens(api_client: TestClient, migrated_postgres_conn: Connection):
    result = await migrated_postgres_conn.fetchval('Select 1')

    assert result == 1
