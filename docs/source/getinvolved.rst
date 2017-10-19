Get Involved
============

Pull code `$ git clone https://github.com/transtats/transtats.git`

Install ansible, docker and vagrant.

::

    $ sudo vagrant up
    $ sudo vagrant ssh

This will setup devel env and run container plus, `ssh` into it.

Run application

::

    $ cd /workspace
    $ make run
    hit localhost:8080 in browser


Create migrations `make migrations`

Run tests `make lint test`

Generate docs `make docs`

Contribution
------------

* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a `GitHub issue <https://github.com/transtats/transtats/issues/new>`_.
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses `travis <https://travis-ci.org/transtats/transtats>`_ for tests.
