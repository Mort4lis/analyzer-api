from aiohttp.web import View
from asyncpgsa import PG


class BaseView(View):
    URL_PATH: str

    @property
    def db(self) -> PG:
        return self.request.app['db']
