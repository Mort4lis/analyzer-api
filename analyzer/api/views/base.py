from aiohttp.web import View, HTTPNotFound
from asyncpgsa import PG
from sqlalchemy import select, exists

from analyzer.db.schema import imports_table


class BaseView(View):
    URL_PATH: str

    @property
    def db(self) -> PG:
        return self.request.app["db"]


class BaseImportView(BaseView):
    @property
    def import_id(self) -> int:
        return int(self.request.match_info.get("import_id"))

    async def check_import_exists(self) -> None:
        """
        Проверяет существание выгрузки.

        Если выгрузка не существует, то выбрасывает исключение.

        :raises
            HTTPNotFound
        """
        query = select([exists().where(imports_table.c.import_id == self.import_id)])

        import_exists = await self.db.fetchval(query=query)
        if not import_exists:
            raise HTTPNotFound
