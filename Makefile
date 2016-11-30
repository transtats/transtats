
.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: devel
devel:
	pip install -r requirements/dev.txt

.PHONY: demo
demo:
	python manage.py runserver 0:8000 --settings=transtats.settings.test --insecure

.PHONY: env
env-info:
	uname -a
	pip list

.PHONY: lint
lint:
	flake8 --ignore=E501,F401,F403,F405 transtats dashboard

.PHONY: migrations
migrations:
	python manage.py makemigrations

.PHONY: migrate
migrate:
	python manage.py migrate

.PHONY: run
run:
	python manage.py runserver
