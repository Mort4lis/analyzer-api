import logging
from functools import partial
from types import MappingProxyType
from typing import Mapping

from aiohttp import PAYLOAD_REGISTRY
from aiohttp.web_app import Application
from configargparse import Namespace

from analyzer.api.payloads import JsonPayload
from analyzer.api.views import VIEWS
from analyzer.utils.db import setup_db

log = logging.getLogger(__name__)


def create_app(args: Namespace) -> Application:
    """Создает экземпляр приложения, готовое к запуску."""
    app = Application()

    # Подключение на старте к postgres и отключение при остановке
    app.cleanup_ctx.append(partial(setup_db, args=args))

    for view in VIEWS:
        log.debug('Registering view %r as %r', view, view.URL_PATH)
        app.router.add_route('*', view.URL_PATH, view)

    # Автоматическая сериализация в json данных в HTTP ответах
    PAYLOAD_REGISTRY.register(JsonPayload, (Mapping, MappingProxyType))
    return app
