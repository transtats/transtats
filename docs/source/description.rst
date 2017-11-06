===============
App Description
===============

Server
======

Graphs
------

1. Translation Status
    Translation progress of a package for most of the branches in all enabled languages.

2. Translation Coverage
    Coverage of a package list for a specific release in associated or selected languages.

3. Translation Workload
    Translation workload estimation for a release branch across packages.

Configuration
-------------

1. Inventory
    Languages & their sets, translation platforms and release streams with their branches are grouped as inventory. Plus upstream.

2. Release Branch
    A particular release which has a schedule and information regarding *in how many languages it will be available*.

3. Packages
    Translation progress would be tracked for added packages. They should have upstream repository URL and translation platform project URL. A package can be linked with multiple release streams and should have a branch mapping.

4. Jobs
    Some functions which are planned to be automated like sync with translation repositories, update release schedule etc. Logs are kept.

5. Graph Rules
    Rules to track translation *as in* coverage of a package list for a specific release branch in a set of languages.

API
---

1. **Ping Server** : :code:`<transtats_server>/api/ping`

    Returns server version.

    .. code-block:: http

        GET /api/ping HTTP/1.1

2. **Package Status** : :code:`<transtats_server>/api/package/<package_name>`

    Returns translation stats of package for enabled languages, for example :code:`abrt`.

    .. code-block:: http

        GET /api/package/abrt HTTP/1.1

3. **Graph Rule Coverage** : :code:`<transtats_server>/api/coverage/<graph_rule_name>`

    Returns translation coverage according to graph rule, for example :code:`rhinstaller`.

    .. code-block:: http

        GET /api/coverage/rhinstaller HTTP/1.1

4. **Release Status** : :code:`<transtats_server>/api/release/<release_branch_name>`

    Returns translation stats of packages which are being tracked for a given release, for example :code:`fedora-27`.

    .. code-block:: http

        GET /api/release/fedora-27 HTTP/1.1

    a. **Release Status Detail** : :code:`<transtats_server>/api/release/<release_branch_name>/detail`

        Returns per language translation stats of packages for a release.

        .. code-block:: http

            GET /api/release/fedora-27/detail HTTP/1.1


Client
======

`transtats-cli <https://github.com/transtats/transtats-cli>`_ is a command line interface to query transtats server.

- **Usage**

    .. code-block:: bash

        $ transtats [OPTIONS] COMMAND [ARGS]...

- **Options**

    --help
        Show help message and exit.

- **Commands**

    1. coverage
        Translation coverage as per graph rule.

    2. package
        Translation status of a package.

    3. version
        Display the current version.

    4. release
        Translation status of a release.
