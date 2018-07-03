==============
Transtats APIs
==============

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

    Returns translation stats of packages which are being tracked for a given release, for example :code:`fedora-29`.

    .. code-block:: http

        GET /api/release/fedora-29 HTTP/1.1

    a. **Release Status Detail** : :code:`<transtats_server>/api/release/<release_branch_name>/detail`

        Returns per language translation stats of packages for a release.

        .. code-block:: http

            GET /api/release/fedora-29/detail HTTP/1.1

    b. **Release Status Locale** : :code:`<transtats_server>/api/release/<release_branch_name>/locale/<locale>`

        Returns translation stats of packages for a release of a single language.

        .. code-block:: http

            GET /api/release/fedora-29/locale/ja_JP HTTP/1.1

5. **Job Details** : :code:`<transtats_server>/api/job/<job-id>/log`

    Returns job log against given job id, for example :code:`2a6d4b23-6a6b-4d0e-b617-a0ece01d790f`.

    .. code-block:: http

        GET /api/job/2a6d4b23-6a6b-4d0e-b617-a0ece01d790f/log  HTTP/1.1
