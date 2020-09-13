import json
from datetime import date
from decimal import Decimal
from functools import singledispatch, partial
from typing import Any

from aiohttp.payload import JsonPayload as BaseJsonPayload
from aiohttp.typedefs import JSONEncoder
from asyncpg import Record

from analyzer.utils.consts import DATE_FORMAT


@singledispatch
def convert(value: Any) -> Any:
    raise NotImplementedError('Unserializable value: {0!r}'.format(value))


@convert.register(Record)
def convert_asyncpg_record(value: Record):
    """
    Позволяет автоматически сериализовать результаты запроса,
    возвращаемые asyncpg.
    """
    return dict(value)


@convert.register(date)
def convert_date(value: date) -> str:
    """
    Позволяет автоматически сериализовать значения
    типа datetime.date.
    """
    return value.strftime(DATE_FORMAT)


@convert.register(Decimal)
def convert_decimal(value: Decimal) -> float:
    """
    Позволяет автоматически сериализовать значения
    типа decimal.Decimal.
    """
    return float(value)


smart_dumps = partial(json.dumps, default=convert, ensure_ascii=False)


class JsonPayload(BaseJsonPayload):
    """
    Заменяет функцию сериализации на более "умную" (умеющую упаковывать в JSON
    объекты asyncpg.Record, datetime.date, decimal.Decimal и другие сущности).
    """

    def __init__(self,
                 *args: Any,
                 dumps: JSONEncoder = smart_dumps,
                 **kwargs: Any) -> None:
        super().__init__(*args, dumps=dumps, **kwargs)
