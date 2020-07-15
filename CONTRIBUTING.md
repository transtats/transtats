# Transtats Server

Hi, we are really excited to see you getting started!

Transtats server is a simple django application. If you have any questions on this or on what may not be covered here, feel free to discuss at `#transtats` channel on `chat.freenode.net`.

## Table of contents

* [Things to know prior contribution](#things-to-know-prior-contribution)
* [Setting up environment](#setting-up-environment)
  * [Try and Test](#try-and-test)
    * [Docker](#docker)
    * [Docker compose](#docker-compose)
  * [Hack and Develop](#hack-and-develop)
    * [Vagrant](#vagrant)
    * [Virtualenv](#virtualenv)
  * [Post Setup Tasks](#post-setup-tasks)
     * [Update db schema](#update-db-schema)
     * [Static Contents](#static-contents)
     * [Create superuser](#create-superuser)
     * [Load demo data](#load-demo-data)
     * [Generate Docs](#generate-docs)
     * [Run celery worker](#run-celery-worker)
     * [Run celery beat](#run-celery-beat)
* [What should I start with?](#what-should-i-start-with)
* [Submitting Pull Requests](#submitting-pull-requests)
* [Reporting Issues](#reporting-issues)

## Things to know prior contribution

- Fork [transtats repo](https://github.com/transtats/transtats) to your username and clone repository locally.
- Setup development environment as described.
- The *devel* branch is the release actively under development.
- The *master* branch corresponds to the latest stable release.
- If you have an idea to discuss, please open a [GitHub Issue](https://github.com/transtats/transtats/issues/new).
- Feel free to submit feature requests and/or bug fixes on *devel* branch.
- Transtats server uses [Circle CI](https://circleci.com/gh/transtats/transtats) for running tests.

## Setting up environment

To try Transtats just pull docker image and spin container or, follow docker-compose path. These environments are based on `test settings` and should contain demo data. Development environments can be created using vagrant or virtualenv.

### Try and Test

#### Docker

Get docker daemon running. Build or pull `transtats` image *([docker.io](https://hub.docker.com/r/transtats/transtats/))* and get started.

- Build the image *(optional)*

  - Clone the repo and build the image 
    ```shell
    $ git clone https://github.com/transtats/transtats.git
    $ cd transtats
    $ sudo docker build -t transtats/transtats deploy/docker
    ```

- Pull the image *(No need to pull, if you have built the image)*
  ```shell
  $ sudo docker pull docker.io/transtats/transtats
  ``` 

- Run the image
  ```shell
  $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats
  ```
  or you can specify custom database credentials using environment variables 
  ```shell
  $ sudo docker run -d --name container_name -p 8080:8015 -e DATABASE_NAME=db_name \
       -e DATABASE_USER=db_user -e DATABASE_PASSWORD=db_passwd transtats/transtats
  ```
  
- Application should be accessible at `localhost:8080`.

#### docker-compose

- Install [docker-compose](https://docs.docker.com/compose) 

- This will clone the repo and start transtats server
  ```shell
  $ git clone https://github.com/transtats/transtats.git
  $ cd transtats/deploy/docker-compose
  $ sudo docker-compose up 
  ```

- Application should be accessible at `localhost:8080`.

### Hack and Develop

#### Vagrant

- Install latest Ansible, Docker and Vagrant.

- This will setup devel environment, run container and `ssh` into it
  ```shell
  $ sudo vagrant plugin install vagrant-hostmanager
  $ git clone https://github.com/transtats/transtats.git
  $ cd transtats
  $ sudo vagrant up
  $ sudo vagrant ssh
  ```

- Run application
  ```shell
  $ cd /workspace
  $ make migrate
  $ make run
  ```

- Application should be accessible at `localhost:8080`.

#### Virtualenv

- Prerequisites `Python 3.x`, `koji`, `cpio`, `patch`, `intltool`, `npm`, `redis`
  ```console
  # Python version should be 3.x
  $ python3 --version

  # Installing other dependencies
  $ sudo dnf install koji cpio patch intltool npm redis
  ```

- This will create virtualenv and setup devel env
  ```shell
  $ git clone https://github.com/transtats/transtats.git; cd transtats
  $ mkvirtualenv transtats --python=`which python3` --system-site-packages
  $ echo `pwd` > /path/to/virtualenvs/transtats/.project
  $ workon transtats; make devel; make migrate; make static
  ```

- Run application
  ```shell
  $ make run
  ```

- Application should be accessible at `localhost:8014`.
  
### Post Setup Tasks

#### Update db schema

If your code changes django models run `make migrations` to update database schema.

#### Static Contents

When you switch `DEBUG` setting to `OFF`, run `make static` to generate static contents.

#### Create superuser

Use `python3 manage.py initlogin` command. And login with `transtats:transtats`.

#### Generate Docs

If your code changes involves something to add in docs, go ahead and generate new docs using `make docs` command. This shall appear at `docs.transtats.org`.

#### Run celery worker

Use `make celeryd` to invoke celery worker. Make sure you're getting a `PONG` from `redis-cli ping` command.

#### Run celery beat

To run async dashboard tasks fire `make celery`. *This will create pid and schedule files.*

## What should I start with?

Broadly we have [enhancement](https://github.com/transtats/transtats/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement), [ui](https://github.com/transtats/transtats/issues?q=is%3Aopen+is%3Aissue+label%3Aui), [docs](https://github.com/transtats/transtats/issues?q=is%3Aopen+is%3Aissue+label%3Adocs) and [test case](https://github.com/transtats/transtats/issues?q=is%3Aopen+is%3Aissue+label%3A%22test+case%22) categories for our backlog of issues. Feel free to make your choice. This would be really helpful if you could browse through existing [issues](https://github.com/transtats/transtats/issues) and [active PRs](https://github.com/transtats/transtats/pulls) before you initiate a feature discussion/development.

## Submitting Pull Request

Submission will go through the GitHub pull request process. Submit your pull request (PR) against the `devel` branch.

- Run `make lint` and fix `flake8` issues if any.
- Make sure `make test` passes on `CI` env.
- Write tests for new functionality or bug fixes.
- Use `git pull --rebase` to keep commit history clean.

## Reporting Issues

If you face any problem feel free to discuss it on `IRC` or open a [GitHub Issue](https://github.com/transtats/transtats/issues/new). We welcome your suggestions and feedback. You may find [issue template](https://github.com/transtats/transtats/blob/devel/.github/ISSUE_TEMPLATE.md) helpful.

