from http import HTTPStatus

from aiohttp.web import Response
from aiohttp_apispec import docs, response_schema

from analyzer.api.schema import TownAgeStatResponseSchema
from analyzer.api.services.stats import get_town_age_statistics
from analyzer.api.views.base import BaseImportView


class TownAgeStatView(BaseImportView):
    URL_PATH = r"/imports/{import_id:\d+}/towns/stat/percentile/age"

    @docs(summary="Статистика возрастов жителей по городам")
    @response_schema(schema=TownAgeStatResponseSchema, code=HTTPStatus.OK.value)
    async def get(self) -> Response:
        await self.check_import_exists()

        stat = await get_town_age_statistics(db=self.db, import_id=self.import_id)
        return Response(body={"data": stat}, status=HTTPStatus.OK.value)
