import os
from pathlib import Path

from alembic.config import Config, CommandLine

from analyzer.utils.db import DEFAULT_PG_URL

PROJECT_PATH = Path(__file__).parent.parent.absolute()


def main():
    alembic = CommandLine()
    alembic.parser.add_argument(
        '--db-url', default=os.getenv('ANALYZER_DB_URL', DEFAULT_PG_URL),
        help='Database URL [env var: ANALYZER_DB_URL]'
    )

    options = alembic.parser.parse_args()
    # Если указан относительный путь до alembic.ini, то добавляем в начало
    # абсолютный путь до приложения
    if not os.path.isabs(options.config):
        options.config = os.path.join(PROJECT_PATH, options.config)

    # Создаем объект конфигурации Alembic
    config = Config(file_=options.config, ini_section=options.name, cmd_opts=options)
    # Меняем значение sqlalchemy.url из конфига Alembic
    config.set_main_option('sqlalchemy.url', options.db_url)

    # Подменяем путь до папки с alembic (требуется, чтобы alembic мог найти env.py, шаблон для
    # генерации миграций и сами миграции)
    alembic_location = config.get_main_option('script_location')
    if not os.path.isabs(alembic_location):
        config.set_main_option('script_location', os.path.join(PROJECT_PATH, alembic_location))

    exit(alembic.run_cmd(config, options))


if __name__ == '__main__':
    main()
