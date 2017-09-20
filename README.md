[![Build Status](https://travis-ci.org/transtats/transtats.svg?branch=master)](https://travis-ci.org/transtats/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

Track translation progress across packages for downstream releases with respect to current development.


### Get Involved


#### try and test: docker


Get docker daemon running. Build or pull `transtats` image *([docker.io](https://hub.docker.com/r/transtats/transtats/))* and get started.

Build or Pull and Run

    1. Clone repo $ git clone https://github.com/transtats/transtats.git
    2. $ cd transtats
    3. $ sudo docker build -t transtats/transtats deploy/docker

    or $ sudo docker pull docker.io/transtats/transtats

    and $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats
    
    or $ sudo docker run -d --name container_name -p 8080:8015 -e DATABASE_NAME=db_name \
         -e DATABASE_USER=db_user -e DATABASE_PASSWD=db_passwd transtats/transtats

Application should be available at `localhost:8080` with `transtats | transtats` as login credentials.


#### develop: vagrant


Pull code `$ git clone https://github.com/transtats/transtats.git`

Install ansible, docker and vagrant.

```shell
$ sudo vagrant up
$ sudo vagrant ssh
```

This will setup devel env and run container plus, `ssh` into it.

Run application

```shell
$ cd /workspace
$ make run
hit localhost:8080 in browser
```

Create migrations `make migrations`

Run tests `make lint test`

Generate docs `make docs`



#### Contribution

* Fork [transtats repo](https://github.com/transtats/transtats) to your username and clone repository locally.
* Setup development environment as described above.
* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a [github issue](https://github.com/transtats/transtats/issues/new).
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses [travis](https://travis-ci.org/transtats/transtats) for tests.


### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
