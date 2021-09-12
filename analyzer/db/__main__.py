import os
from pathlib import Path

from alembic.config import CommandLine

from analyzer.utils.consts import DEFAULT_PG_URL
from analyzer.utils.db import make_alembic_config

PROJECT_PATH = Path(__file__).parent.parent.absolute()


def main():
    alembic = CommandLine()
    alembic.parser.add_argument(
        "--db-url",
        default=os.getenv("ANALYZER_DB_URL", DEFAULT_PG_URL),
        help="Database URL [env var: ANALYZER_DB_URL]",
    )

    options = alembic.parser.parse_args()
    config = make_alembic_config(options)

    exit(alembic.run_cmd(config, options))


if __name__ == "__main__":
    main()
