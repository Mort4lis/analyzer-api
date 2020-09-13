from functools import partial

from aiohttp.web_app import Application
from configargparse import Namespace

from analyzer.utils.db import setup_db


def create_app(args: Namespace) -> Application:
    """Создает экземпляр приложения, готовое к запуску."""
    app = Application()

    # Подключение на старте к postgres и отключение при остановке
    app.cleanup_ctx.append(partial(setup_db, args=args))

    return app
