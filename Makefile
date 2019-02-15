
.PHONY: celeryd
celeryd:
	celery -A transtats worker -l info

.PHONY: celery
celery:
	celery -A transtats beat -l info -S django_celery_beat.schedulers:DatabaseScheduler

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: devel
devel:
	pip3 install -r requirements/dev.txt

.PHONY: docs
docs:
	cd docs; make html

.PHONY: demo
demo:
	python3 manage.py runserver 0:8015 --settings=transtats.settings.test

.PHONY: env-info
env-info:
	uname -a
	pip list

.PHONY: lint
lint:
	flake8 --ignore=E501,F401,F403,F405 transtats dashboard

.PHONY: migrations
migrations:
	python3 manage.py makemigrations

.PHONY: migrate
migrate:
	python3 manage.py migrate

.PHONY: run
run:
	python3 manage.py runserver 0:8014

.PHONY: static
static:
	python3 manage.py collectstatic --noinput

.PHONY: test
test:
	python3 manage.py test dashboard.tests -v 2 --settings=transtats.settings.test
