=============
Transtats CLI
=============

`transtats-cli <https://github.com/transtats/transtats-cli>`_ is a command line interface to query transtats server.

- **Configuration**

    ``transtats.conf`` should be placed inside ``~/.config/`` directory.
    Transtats server url and API token can be added as

    .. code-block:: bash

        [server]
        server_url = http://transtats.fedoraproject.org
        token = <API-token-from-server>


- **Usage**

    .. code-block:: bash

        $ transtats [OPTIONS] COMMAND [ARGS]...

- **Options**

    --help
        Show help message and exit.

- **Commands**

    1. coverage
        Translation coverage as per graph rule.

        .. code-block:: bash

            transtats coverage [OPTIONS] GRAPH_RULE

    2. job
        Runs a job and/or show the job log.

        .. code-block:: bash

            transtats job [OPTIONS] COMMAND [ARGS]...

    3. package
        Translation status of a package.

        .. code-block:: bash

            transtats package [OPTIONS] PACKAGE_NAME

    4. version
        Display the current version.

        .. code-block:: bash

            transtats version [OPTIONS]

    5. release
        Translation status of a release.

        .. code-block:: bash

            transtats release [OPTIONS] RELEASE_SLUG
