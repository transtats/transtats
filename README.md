[![CircleCI](https://circleci.com/gh/transtats/transtats.svg?style=svg)](https://circleci.com/gh/transtats/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

Track translation progress across packages for downstream releases with respect to current development.


### Get Involved


#### Try and test

##### Docker

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
  
- Application should be available at `localhost:8080`.

##### docker-compose

- Install [docker-compose](https://docs.docker.com/compose) 

- This will clone the repo and start transtats server
  ```shell
  $ git clone https://github.com/transtats/transtats.git
  $ cd transtats/deploy/docker-compose
  $ sudo docker-compose up 
  ```

- Application should be available at `localhost:8080`. 


#### Hacking: Setup Development Environment


##### Vagrant

- Install Ansible, Docker and Vagrant.

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
  $ make run
  ```

- Hit `localhost:8080` in browser


##### Virtualenv

- Install py3.6, koji, cpio

- This will create virtualenv and setup devel env
  ```shell
  $ git clone https://github.com/transtats/transtats.git
  $ cd transtats
  $ mkvirtualenv transtats --python=`which python3.6` --system-site-packages
  $ echo `pwd` > /path/to/virtualenvs/transtats/.project
  $ workon transtats; make devel; make migrate
  ```

- Run application
  ```shell
  $ make run
  ```

- Hit `localhost:8014` in browser


##### Tasks

- Update db schema `make migrations`

- Run tests `make lint test`

- Create static contents `make static`

- Generate docs `make docs`


#### Contribution

* Fork [transtats repo](https://github.com/transtats/transtats) to your username and clone repository locally.
* Setup development environment as described above.
* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a [GitHub Issue](https://github.com/transtats/transtats/issues/new).
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses [Circle CI](https://circleci.com/gh/transtats/transtats) for tests.


### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0

