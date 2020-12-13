import os
from typing import Generator
from uuid import uuid4

import pytest
from alembic.config import Config
from configargparse import Namespace
from sqlalchemy_utils import create_database, drop_database
from yarl import URL

from analyzer.utils.consts import DEFAULT_PG_URL
from analyzer.utils.db import make_alembic_config

PG_URL = os.getenv('ANALYZER_DB_URL', DEFAULT_PG_URL)


@pytest.fixture
def postgres() -> Generator[str, None, None]:
    db_name = '.'.join([uuid4().hex, 'pytest'])
    test_pg_url = str(URL(PG_URL).with_name(db_name))
    create_database(url=test_pg_url)

    try:
        yield test_pg_url
    finally:
        drop_database(test_pg_url)


@pytest.fixture
def alembic_config(postgres: str) -> Config:
    options = Namespace(
        config='alembic.ini', name='alembic',
        db_url=postgres, raiseerr=False, x=None
    )
    return make_alembic_config(options)
