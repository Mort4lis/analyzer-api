from http import HTTPStatus

from aiohttp.web import Response
from aiohttp_apispec import request_schema, docs, response_schema

from analyzer.api.schema import PatchCitizenRequestSchema, PatchCitizenResponseSchema
from analyzer.api.services.citizens import get_citizens_cursor, partially_update_citizen
from analyzer.api.views.base import BaseImportView


class CitizenListView(BaseImportView):
    URL_PATH = r'/imports/{import_id:\d+}/citizens'

    @docs(summary='Отобразить информацию о всех жителях для указанной выборки')
    async def get(self) -> Response:
        """
        Возвращает информацию о всех выжетелях указанной выборки.

        Сразу возвращает клиенту HTTP-ответ со статусом 200 OK.
        И "находу" формирует payload (информацию о жителях).

        Этот подход позволяет не выделять память на весь объем данных при каждом запросе,
        но у него есть особенность: приложение не сможет вернуть клиенту соответствующий HTTP-статус,
        если возникнет ошибка (ведь клиенту уже был отправлен HTTP-статус, заголовки, и пишутся данные).
        """
        await self.check_import_exists()
        cursor = get_citizens_cursor(db=self.db, import_id=self.import_id)
        return Response(body=cursor, status=HTTPStatus.OK.value)


class CitizenDetailView(BaseImportView):
    URL_PATH = r'/imports/{import_id:\d+}/citizens/{citizen_id:\d+}'

    @property
    def citizen_id(self) -> int:
        return int(self.request.match_info.get('citizen_id'))

    @docs(summary='Обновить указанного жителя в указанной выгрузке')
    @request_schema(schema=PatchCitizenRequestSchema)
    @response_schema(schema=PatchCitizenResponseSchema, code=HTTPStatus.OK.value)
    async def patch(self) -> Response:
        """Частичное обновление жителя указанной выгрузки."""
        updated_citizen = await partially_update_citizen(
            db=self.db,
            import_id=self.import_id,
            citizen_id=self.citizen_id,
            updated_data=self.request['data']
        )
        return Response(body={'data': updated_citizen}, status=HTTPStatus.OK.value)
