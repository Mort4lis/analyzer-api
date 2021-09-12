import logging
from functools import partial
from types import MappingProxyType, AsyncGeneratorType
from typing import Mapping, AsyncIterable

from aiohttp import PAYLOAD_REGISTRY
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware
from configargparse import Namespace

from analyzer.api.middlewares import error_middleware, format_validation_error
from analyzer.api.payloads import JsonPayload, AsyncGenJSONListPayload
from analyzer.api.views import VIEWS
from analyzer.utils.consts import MAX_REQUEST_SIZE
from analyzer.utils.db import setup_db

log = logging.getLogger(__name__)


def create_app(args: Namespace) -> Application:
    """Создает экземпляр приложения, готовое к запуску."""
    app = Application(
        middlewares=[error_middleware, validation_middleware],
        client_max_size=MAX_REQUEST_SIZE,
    )

    # Подключение на старте к postgres и отключение при остановке
    app.cleanup_ctx.append(partial(setup_db, args=args))

    for view in VIEWS:
        log.debug("Registering view %r as %r", view, view.URL_PATH)
        app.router.add_route("*", view.URL_PATH, view)

    setup_aiohttp_apispec(
        app=app,
        title="Citizens API",
        swagger_path="/",
        error_callback=format_validation_error,
    )

    # Автоматическая сериализация в json данных в HTTP ответах
    PAYLOAD_REGISTRY.register(JsonPayload, (Mapping, MappingProxyType))
    PAYLOAD_REGISTRY.register(AsyncGenJSONListPayload, (AsyncGeneratorType, AsyncIterable))
    return app
