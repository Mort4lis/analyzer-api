import logging
from typing import AsyncIterable, AsyncIterator

from aiohttp.web import Application
from asyncpgsa import PG
from asyncpgsa.transactionmanager import ConnectionTransactionContextManager
from configargparse import Namespace
from sqlalchemy import Numeric, cast, func
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

log = logging.getLogger(__name__)


async def setup_db(app: Application, args: Namespace):
    """
    Подключение и отключение БД.

    До оператора yield выполняется инициализация подключения к БД, создание
    пула коннектов и т.д.
    То, что после оператора yield - закрытие всех соединений и освобождение ресурсов.

    :param app: экземпляр приложения
    :param args: аргументы командной строки
    """
    app['db'] = PG()
    await app['db'].init(
        str(args.pg_url),
        min_size=args.pg_pool_min_size,
        max_size=args.pg_pool_max_size
    )

    await app['db'].fetchval('SELECT 1')
    log.info('Connected to database')

    try:
        yield
    finally:
        log.info('Disconnecting from database')
        await app['db'].pool.close()
        log.info('Disconnected from database')


class AsyncPGCursor(AsyncIterable):
    """
    Обёртка над курсором из asyncpg.

    Используется, чтобы отправлять данные из PostgreSQL клиенту по частям.
    Объкты данного класса являются Iterable (то есть, по которым можно проитерироваться).
    А именно, должен быть реализован метод __iter__, возвращающий итератор
    (или __aiter__ в случае асинхронности).
    """
    PREFETCH = 500

    __slots__ = (
        'query', 'transaction_ctx',
        'prefetch', 'timeout'
    )

    def __init__(self,
                 query: Select,
                 transaction_ctx: ConnectionTransactionContextManager,
                 prefetch: int = None,
                 timeout: float = None) -> None:
        self.query = query
        self.transaction_ctx = transaction_ctx
        self.prefetch = prefetch or self.PREFETCH
        self.timeout = timeout

    async def __aiter__(self) -> AsyncIterator:
        """
        Возвращает асинхронный генератор (который является итератором).

        Является генераторной функцией, при вызове которой возвращается
        генератор (итератор), который имеет метод __next__ (__anext__)
        для перебора значений.

        """
        async with self.transaction_ctx as conn:
            cursor = conn.cursor(self.query, prefetch=self.prefetch, timeout=self.timeout)
            async for row in cursor:
                yield row


def rounded(column: ColumnElement, fraction: int = 2) -> ColumnElement:
    return func.round(cast(column, Numeric), fraction)
