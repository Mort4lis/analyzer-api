from http import HTTPStatus

from aiohttp.web import Response
from aiohttp_apispec import request_schema, docs, response_schema

from analyzer.api.schema import ImportRequestSchema, ImportResponseSchema
from analyzer.api.services.imports import create_import
from analyzer.api.views.base import BaseView


class ImportView(BaseView):
    URL_PATH = '/imports'

    @docs(summary='Добавить выгрузку с информацией о житилях')
    @request_schema(schema=ImportRequestSchema)
    @response_schema(schema=ImportResponseSchema, code=HTTPStatus.CREATED.value)
    async def post(self) -> Response:
        import_id = await create_import(
            db=self.db,
            citizens=self.request['data']['citizens']
        )
        return Response(body={
            'data': {'import_id': import_id}
        }, status=HTTPStatus.CREATED.value)
