postgres:
	docker stop analyzer-postgres || true
	docker run --rm --detach --name=analyzer-postgres \
		--env POSTGRES_USER=analyzer_user \
		--env POSTGRES_PASSWORD=analyzer_password \
		--env POSTGRES_DB=analyzer \
		--publish 5432:5432 postgres:12.1

test:
	venv/bin/pytest --cov=analyzer --cov-report=term-missing tests/

sdist:
	python setup.py sdist

migrate:
	analyzer-db upgrade head

downgrade:
	analyzer-db downgrade -1