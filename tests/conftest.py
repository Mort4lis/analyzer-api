import os
from typing import Generator

import pytest
from alembic.command import upgrade
from alembic.config import Config
from yarl import URL

from analyzer.utils.consts import DEFAULT_PG_URL
from analyzer.utils.db import tmp_database, alembic_config_from_url

PG_URL = os.getenv("ANALYZER_DB_URL", DEFAULT_PG_URL)


@pytest.fixture(scope="session")
def migrated_postgres_template() -> Generator[str, None, None]:
    """
    Создает шаблон БД и применяет все миграции.

    БД используется в качестве шаблона для быстрого создания независимых БД для тестов.
    Область видимости "session" гарантирует, что данная фикстура будет вызвана один раз
    при запуске всех тестов.
    """
    with tmp_database(db_url=PG_URL, suffix="template") as db_url:
        alembic_config = alembic_config_from_url(db_url)
        upgrade(config=alembic_config, revision="head")
        yield db_url


@pytest.fixture
def migrated_postgres(migrated_postgres_template: str) -> Generator[str, None, None]:
    """
    Создает БД на основе шаблона с примененными миграциями.

    Данная фикстура используется для тестов, которым необходим доступ к БД со всеми миграциями.
    """
    template_db = URL(migrated_postgres_template).name
    with tmp_database(db_url=PG_URL, suffix="pytest", template=template_db) as db_url:
        yield db_url


@pytest.fixture
def alembic_config() -> Generator[Config, None, None]:
    with tmp_database(db_url=PG_URL, suffix="pytest") as db_url:
        config = alembic_config_from_url(db_url)
        yield config
