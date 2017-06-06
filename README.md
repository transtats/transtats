[![Build Status](https://travis-ci.org/transtats/transtats.svg?branch=master)](https://travis-ci.org/transtats/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

Track translation progress across packages for downstream releases with respect to current development.

### Get Involved

#### try and test: docker

Get docker daemon running. Build or pull `transtats` image *([docker.io](https://hub.docker.com/r/transtats/transtats/))* and get started.

Build or Pull and Run

    1. Clone repo $ git clone https://github.com/transtats/transtats.git
    2. $ cd transtats/deploy/docker
    3. $ sudo docker build -t transtats .

    or $ sudo docker pull docker.io/transtats/transtats

    and $ sudo docker run -d --name container_name -p 8080:8015 transtats

Application should be available at `localhost:8080` with `transtats | transtats` as login credentials.



#### develop: virtualenv

Setup [Virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html) and [PostgreSQL 9.5](https://fedoraproject.org/wiki/PostgreSQL). Create virtualenv. Clone repo.

```shell
workon transtats
cd /path/to/transtats/repo
make devel
```

Create `transtats` database. Copy `keys.json.example` to `keys.json` and put your values.

```shell
make migrate && make run
```

Run tests   `make lint test`

Generate docs   `make docs`

#### Contribution

* Fork [transtats repo](https://github.com/transtats/transtats) to your username and clone repository locally.
* Set up a development environment as described above.
* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a [github issue](https://github.com/transtats/transtats/issues/new).
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses [travis](https://travis-ci.org/transtats/transtats) for tests.


### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
