import logging
from http import HTTPStatus
from typing import Callable, Mapping

from aiohttp.web import Request, Response, middleware
from aiohttp.web_exceptions import (
    HTTPException,
    HTTPBadRequest,
    HTTPInternalServerError
)
from marshmallow.validate import ValidationError

from analyzer.api.payloads import JsonPayload

logger = logging.getLogger(__name__)


def format_http_exception(exc: HTTPException, fields: Mapping = None) -> HTTPException:
    """
    Изменяет формат исключения `HTTPException`.

    Создает новый экземпляр `HTTPException` с другим форматом:

    {
      "code": "http_verbose_code",
      "message": "description",
      "fields": {
        "field1": "verbose_message",
        "field2": "verbose_message",
        ...
      }
    }

    :param exc: экземпляр http-исключения
    :param fields: поля
    :return: новый экземпляр http-исключения
    """
    http_status = HTTPStatus(exc.status_code)
    body = {
        'code': http_status.name.lower(),
        'message': exc.text or http_status.descripton
    }

    if fields:
        body['fields'] = fields

    return exc.__class__(body=body)


def format_validation_error(err: ValidationError, *_) -> HTTPException:
    """
    Изменяет формат исключения `ValidationError` на `HTTPException`.

    :param err: экземпляр validation-исключения
    :raise HTTPException
    """
    raise format_http_exception(
        exc=HTTPBadRequest(text='Request validation has failed'),
        fields=err.messages
    )


@middleware
async def error_middleware(request: Request, handler: Callable) -> Response:
    """
    Middleware, обрабатывающий исключения, выброшенные в handler'ах.

    :param request: экземпляр aiohttp-запроса
    :param handler: обработчик
    :return: экземпляр aiohttp-ответа
    """
    try:
        return await handler(request)
    except HTTPException as exc:
        # Текстовые исключения (или исключения без информации)
        # форматируем в JSON
        if not isinstance(exc.body, JsonPayload):
            exc = format_http_exception(exc=exc)
        raise exc

    except ValidationError as err:
        raise format_validation_error(err=err)

    except Exception as exc:
        logger.exception(exc)
        raise format_http_exception(exc=HTTPInternalServerError())
