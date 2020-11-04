import json
from datetime import date
from decimal import Decimal
from functools import singledispatch, partial
from typing import Any, AsyncIterator

from aiohttp.abc import AbstractStreamWriter
from aiohttp.payload import JsonPayload as BaseJsonPayload, Payload
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


class AsyncGenJSONListPayload(Payload):
    def __init__(self,
                 value: AsyncIterator,
                 encoding: str = 'utf-8',
                 content_type: str = 'application/json',
                 root_object: str = 'data',
                 *args,
                 **kwargs):
        self.root_object = root_object
        super().__init__(
            value=value,
            encoding=encoding,
            content_type=content_type,
            *args, **kwargs
        )

    async def write(self, writer: AbstractStreamWriter) -> None:
        """
        Итерируется построчно по асинхронному итератору и пишет ответ клиенту.

        Итеративно формируется ответ вида:
        {
            data: [
                {
                    "field1": "",
                    "field2": ""
                },
                ...
            ]
        }
        """
        # начало объекта
        await writer.write(
            '{{"{0}":['.format(self.root_object).encode(self.encoding)
        )

        first = True
        async for row in self._value:
            # перед первой строчкой запятая не нужна
            if not first:
                # ставим запятую
                await writer.write(b',')

            await writer.write(
                smart_dumps(row).encode(self.encoding)
            )

        # конец объекта
        await writer.write(b']}')
