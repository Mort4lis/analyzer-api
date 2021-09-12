import os
from typing import Callable

from aiohttp import web
from aiomisc.log import LogFormat, basic_config
from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from yarl import URL

from analyzer.api.app import create_app
from analyzer.utils.consts import ENV_VAR_PREFIX, DEFAULT_PG_URL

parser = ArgumentParser(
    # Парсер будет искать переменные окружения с префиксом ANALYZER_,
    # например ANALYZER_API_ADDRESS и ANALYZER_API_PORT
    auto_env_var_prefix=ENV_VAR_PREFIX,
    # Покажет значения параметров по умолчанию
    formatter_class=ArgumentDefaultsHelpFormatter,
)

group = parser.add_argument_group("API Options")
group.add_argument(
    "--api-address",
    default="0.0.0.0",
    help="IPv4/IPv6 address API server would listen on",
)
group.add_argument("--api-port", type=int, default=8081, help="TCP port API server would listen on")

group = parser.add_argument_group("PostgreSQL options")
group.add_argument(
    "--pg-url",
    type=URL,
    default=URL(DEFAULT_PG_URL),
    help="URL to use to connect to the database",
)
group.add_argument("--pg-pool-min-size", type=int, default=10, help="Minimum database connections")
group.add_argument("--pg-pool-max-size", type=int, default=10, help="Maximum database connection")

group = parser.add_argument_group("Logging options")
group.add_argument(
    "--log-level",
    default="debug",
    choices=("debug", "info", "warning", "error", "fatal"),
)
group.add_argument("--log-format", default="color", choices=LogFormat.choices())


def clean_environ(rule: Callable):
    """Очистка переменных окружения по определенному правилу."""
    for var in filter(rule, tuple(os.environ)):
        os.environ.pop(var)


def main():
    args = parser.parse_args()

    # После получения конфигурации приложения переменные окружения приложения
    # больше не нужны и даже могут представлять опасность - например, они могут
    # случайно "утечь" с отображением информации об ошибке. Злоумышленники
    # в первую очередь будут пытаться получить информацию об окружении, очистка
    # переменных окружения считается хорошим тоном.

    # Python позволяет управлять поведением stdlib модулей с помощью
    # многочисленных переменных окружения, разумно очищать переменные окружения
    # по префиксу приложения, указанного в ConfigArgParser.
    clean_environ(rule=lambda var: var.startswith(ENV_VAR_PREFIX))

    # Чтобы логи не блокировали основной поток (и event loop) во время операций
    # записи в stderr или файл - логи можно буфферизовать и обрабатывать в
    # отдельном потоке (aiomisc.basic_config настроит буфферизацию
    # автоматически).
    basic_config(level=args.log_level, log_format=args.log_format, buffered=True)

    app = create_app(args=args)
    web.run_app(app=app, host=args.api_address, port=args.api_port)


if __name__ == "__main__":
    main()
