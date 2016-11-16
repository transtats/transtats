.PHONY: clean-pyc

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

devel:
	pip install -r requirements/dev.txt

fire:
	python manage.py runserver 0:8000 --settings=transtats.settings.test --insecure

lint:
	flake8 --ignore=E501,F401,F403,F999 transtats dashboard

migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

run:
	python manage.py runserver
