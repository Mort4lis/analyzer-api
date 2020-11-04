from analyzer.api.views.base import BaseImportView
from aiohttp.web import Response
from aiohttp_apispec import docs

from analyzer.api.services.citizens import get_citizens_cursor


class CitizenView(BaseImportView):
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
        return Response(body=cursor)
