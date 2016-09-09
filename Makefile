.PHONY: clean-pyc

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

devel:
	pip install -r requirements/dev.txt

fire:
	python transtats/manage.py runserver 0:8000 --settings=config.settings.test --insecure

lint:
	flake8 --ignore=E501,F401,F403 transtats

migrate:
	alembic -h
