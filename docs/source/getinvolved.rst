Get Involved
============

Welcome! Read Transtats `Contributing Guide <https://github.com/transtats/transtats/blob/devel/CONTRIBUTING.md>`_ for getting started.

Try and test
-------------

- **Docker**

  Get docker daemon running. Build or pull `transtats image <https://hub.docker.com/r/transtats/transtats>`_  and get started.

  - Build the image *(optional)*

    - Clone the repo and build the image
       .. code-block:: bash

          $ git clone https://github.com/transtats/transtats.git
          $ cd transtats
          $ sudo docker build -t transtats/transtats deploy/docker

  - Pull the image *(No need to pull, if you have built the image)*
      .. code-block:: bash

          $ sudo docker pull docker.io/transtats/transtats

  - Run the image
      .. code-block:: bash

          $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats

    or you can specify custom database credentials using environment variables
      .. code-block:: bash

          $ sudo docker run -d --name container_name -p 8080:8015 -e DATABASE_NAME=db_name \
                 -e DATABASE_USER=db_user -e DATABASE_PASSWD=db_passwd transtats/transtats

  - Application should be available at :code:`localhost:8080` with :code:`transtats | transtats` as login credentials.


Hack and Develop
----------------

- Install and run Ansible, Docker and Vagrant.

- This will setup devel environment and run container plus, `ssh` into it
    .. code-block:: bash

        $ sudo vagrant plugin install vagrant-hostmanager
        $ git clone https://github.com/transtats/transtats.git
        $ cd transtats
        $ sudo vagrant up
        $ sudo vagrant ssh

- Run application
    .. code-block:: bash

        $ cd /workspace
        $ make run

- Hit :code:`localhost:8080` in browser

- Create migrations :code:`make migrations`

- Collect static files :code:`make static`

- Run tests :code:`make lint test`

- Generate docs :code:`make docs`


Contribute
----------

* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a `GitHub issue <https://github.com/transtats/transtats/issues/new>`_.
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses `CircleCI <https://circleci.com/gh/transtats/transtats>`_ for tests.
