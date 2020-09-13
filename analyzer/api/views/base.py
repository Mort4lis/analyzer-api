from aiohttp.web import View


class BaseView(View):
    URL_PATH: str

    @property
    def db(self):
        return self.request.app['db']
