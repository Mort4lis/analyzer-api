from typing import Callable, AsyncGenerator

import asyncpg
import pytest
from aiohttp.test_utils import TestClient
from configargparse import Namespace

from analyzer.api.__main__ import parser
from analyzer.api.app import create_app


@pytest.fixture
def arguments(aiomisc_unused_port: int, migrated_postgres: str) -> Namespace:
    """Аргументы для запуска приложения."""
    return parser.parse_args([
        '--api-port={0}'.format(aiomisc_unused_port),
        '--pg-url={0}'.format(migrated_postgres)
    ])


@pytest.fixture
async def api_client(aiohttp_client: Callable, arguments: Namespace) -> AsyncGenerator[TestClient, None]:
    """Создает и запускает приложение и возвращает клиента для выполнения запросов."""
    app = create_app(arguments)
    client = await aiohttp_client(app, server_kwargs={
        'port': arguments.api_port
    })

    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def migrated_postgres_conn(migrated_postgres: str) -> AsyncGenerator[asyncpg.Connection, None]:
    conn = await asyncpg.connect(dsn=migrated_postgres)

    try:
        yield conn
    finally:
        await conn.close()
