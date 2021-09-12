# Analyzer REST API
![ci-workflow](https://github.com/Mort4lis/analyzer-api/actions/workflows/main.yml/badge.svg)
![coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)
![python-versions](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![code-size](https://img.shields.io/github/languages/code-size/Mort4lis/analyzer-api)
![code-lines](https://img.shields.io/tokei/lines/github/Mort4lis/analyzer-api)
![image-size](https://img.shields.io/docker/image-size/mortalis/analyzer-api/latest)

## Описание

Решение вступительного задания в школу бэкенд-разработки Яндекса ([ссылка на задание](./docs/task.pdf)).
Данный проект реализовался в целях обучения: поработать с `aiohttp`, `pytest`, `docker`, `github-actions`.

## Как использовать?

Перед тем как запустить приложение необходимо поднять `postgres` в docker-контейнере,
либо вручную.

```bash
$ docker run --rm --detach --name=analyzer-postgres \
		--env POSTGRES_USER=analyzer_user \
		--env POSTGRES_PASSWORD=analyzer_password \
		--env POSTGRES_DB=analyzer \
		--publish 5432:5432 postgres:12.1
```

### Используя [Docker](https://www.docker.com/ "Docker")
1. Загружаем docker-образ
```bash
$ docker pull mortalis/analyzer-api:latest
```
2. Применяем миграции
```bash
$ docker run --network=host mortalis/analyzer-api:latest analyzer-db upgrade head
```
3. Запускаем приложение
```bash
$ docker run --network=host --detach mortalis/analyzer-api:latest
```

### Склонировав проект
1. Клонируем проект с репозитория
```bash
$ git clone https://github.com/Mort4lis/analyzer-api.git
$ cd enrollment_2019/
```
2. (Необязательно) Можно создать виртуальное окружение, для того чтобы изолировать данный
пакет
```bash
$ python -m venv venv
$ source venv/bin/activate
```
3. Устанавливаем пакет, после установки которого у нас появятся две cli-команды 
`analyzer-api` и `analyzer-db`
```bash
$ pip install .
```
3. Применяем миграции
```bash
$ make migrate
# или
$ analyzer-db upgrade head
```
4. Запускаем приложение
```bash
$ analyzer-api
```

## Swagger-документация
После запуска, приложение по-умолчанию будет доступно на 8081 порту.
Для просмотра swagger-документации перейдите по http://127.0.0.1:8081/

## Конфигурация приложения

Приложение можно конфигурировать cli-аргументами и переменными окружения среды (`environment variables`).
Получить более подробную информацию о списке аргументов:
```bash
# пример с docker
$ docker run --network=host mortalis/analyzer-api:latest analyzer-api --help
# пример с cli
$ analyzer-api --help
```

Полный список переменных окружения для конфигурации:
* `ANALYZER_API_ADDRESS` - IPv4/IPv6-адрес, который будет слушать сервис
* `ANALYZER_API_PORT` - tcp-порт, который будет слушать сервис
* `ANALYZER_PG_URL` - dsn для подключения к `postgres`
* `ANALYZER_PG_POOL_MIN_SIZE` - минимальный размер пула соединений к `postgres`
* `ANALYZER_PG_POOL_MAX_SIZE` - максимальный размер пула соединений к `postgres`
* `ANALYZER_LOG_LEVEL` - уровень логирования (`debug`, `info`, `warning`, `error`, `fatal`)
* `ANALYZER_LOG_FORMAT`- формат лога (`stream`, `color`, `json`, `syslog`)

Например, можно запустить приложение на порту 8081, указав другое dsn для подключение к `postgres`:
```bash
$ docker run --network=host --detach \
  --env ANALYZER_PG_URL=postgresql://another_user:another_password@localhost/another_db \
  mortalis/analyzer-api:latest
```

## Запуск тестов
Для запуска тестов и просмотра процента покрытия кодовой базы необходимо 
склонировать проект, находиться в папке с проектом и установить пакет в "режиме разработки".
```bash
$ pip install '.[dev]'
```

Запуск тестов
```bash
$ make test
# или
pytest --cov=analyzer --cov-report=term-missing tests/
```