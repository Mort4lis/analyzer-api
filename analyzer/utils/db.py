import logging
import os
import uuid
from contextlib import contextmanager
from typing import AsyncIterable, AsyncIterator, Generator

from aiohttp.web import Application
from alembic.config import Config
from asyncpgsa import PG
from asyncpgsa.transactionmanager import ConnectionTransactionContextManager
from configargparse import Namespace
from sqlalchemy import Numeric, cast, func
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy_utils import create_database, drop_database
from yarl import URL

from analyzer.utils.consts import PROJECT_PATH

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
    app["db"] = PG()
    await app["db"].init(str(args.pg_url), min_size=args.pg_pool_min_size, max_size=args.pg_pool_max_size)

    await app["db"].fetchval("SELECT 1")
    log.info("Connected to database")

    try:
        yield
    finally:
        log.info("Disconnecting from database")
        await app["db"].pool.close()
        log.info("Disconnected from database")


class AsyncPGCursor(AsyncIterable):
    """
    Обёртка над курсором из asyncpg.

    Используется, чтобы отправлять данные из PostgreSQL клиенту по частям.
    Объкты данного класса являются Iterable (то есть, по которым можно проитерироваться).
    А именно, должен быть реализован метод __iter__, возвращающий итератор
    (или __aiter__ в случае асинхронности).
    """

    PREFETCH = 500

    __slots__ = ("query", "transaction_ctx", "prefetch", "timeout")

    def __init__(
        self,
        query: Select,
        transaction_ctx: ConnectionTransactionContextManager,
        prefetch: int = None,
        timeout: float = None,
    ) -> None:
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


def make_alembic_config(options: Namespace, base_path: str = PROJECT_PATH) -> Config:
    """
    Создает объект конфигурации alembic на основе аргументов командной строки,
    и настраивает его (меняет относительные пути на абсолютные).

    :param options: аргументы командной строки
    :param base_path: путь, относительного которого формируются относительные пути
    :return: объект конфигурации alembic
    """
    # Если указан относительный путь до alembic.ini, то добавляем в начало base_path
    # (формируем абсолютный путь)
    if not os.path.isabs(options.config):
        options.config = os.path.join(base_path, options.config)

    # Создаем объект конфигурации Alembic
    config = Config(file_=options.config, ini_section=options.name, cmd_opts=options)
    if options.db_url:
        # Меняем значение sqlalchemy.url из конфига Alembic
        config.set_main_option("sqlalchemy.url", options.db_url)

    # Подменяем путь до папки с alembic (требуется, чтобы alembic мог найти env.py, шаблон для
    # генерации миграций и сами миграции)
    alembic_location = config.get_main_option("script_location")
    if not os.path.isabs(alembic_location):
        config.set_main_option("script_location", os.path.join(base_path, alembic_location))

    return config


@contextmanager
def tmp_database(
    db_url: str,
    suffix: str = "",
    encoding: str = "utf8",
    template: str = None,
) -> Generator[str, None, None]:
    db_name = ".".join([uuid.uuid4().hex, suffix])
    db_url = str(URL(db_url).with_name(db_name))
    create_database(url=db_url, encoding=encoding, template=template)

    try:
        yield db_url
    finally:
        drop_database(url=db_url)


def alembic_config_from_url(db_url: str = None) -> Config:
    options = Namespace(config="alembic.ini", name="alembic", db_url=db_url, raiseerr=False, x=None)
    return make_alembic_config(options)
