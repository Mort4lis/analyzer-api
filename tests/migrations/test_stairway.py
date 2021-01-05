from typing import List

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import Script, ScriptDirectory

from analyzer.utils.db import alembic_config_from_url


def get_revisions() -> List[Script]:
    # Создаем объект с конфигурацей alembic (для получения списка миграций БД
    # не нужна).
    config = alembic_config_from_url()

    # Получаем директорию с миграциями alembic
    revisions_dir = ScriptDirectory.from_config(config)

    # Получаем миграции и сортируем в порядке от первой до последней
    revisions = list(revisions_dir.walk_revisions())
    revisions.reverse()
    return revisions


@pytest.mark.parametrize('revision', get_revisions())
def test_migrations_stairway(alembic_config: Config, revision: Script) -> None:
    upgrade(alembic_config, revision.revision)
    # -1 используется для downgrade первой миграции (т.к. ее down_revision
    # равен None)
    downgrade(alembic_config, revision.down_revision or '-1')
    upgrade(alembic_config, revision.revision)
