from http import HTTPStatus

from aiohttp.web import Response

from analyzer.api.views.base import BaseView


class ImportView(BaseView):
    URL_PATH = '/imports'

    async def get(self) -> Response:
        return Response(body={'hello': 'world'}, status=HTTPStatus.OK)
