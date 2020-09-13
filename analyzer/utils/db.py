import logging

from aiohttp.web import Application
from asyncpgsa import PG
from configargparse import Namespace

DEFAULT_PG_URL = 'postgresql://analyzer_user:analyzer_password@localhost/analyzer'

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
