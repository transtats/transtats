=======
Roadmap
=======

| As the project evolves, a roadmap will be published for each major release. Comments, suggestions, and requests to the current roadmap are welcome. Our goal in publishing a roadmap is transparency and community inclusion.
| A roadmap is the team's best guess based on experience, community requests, and feedback.

Transtats 0.8.0
===============

| We are currently working on :code:`0.8.0` release.
| See `Changelog <https://github.com/transtats/transtats/blob/devel/CHANGELOG.md>`_

| Backlog is `here <https://github.com/transtats/transtats/issues>`_. For release features list please look at `milestone <https://github.com/transtats/transtats/milestone/11>`_.
| Target delivery: By end of May 2019

To Do
=====

- Manage Inventory
    - Languages and their Sets (Done)
    - Translation Platforms (Done)
    - Product and their Releases (Done)

- Translation Status of Packages, sync with:
    - Translation Platform (Done)
        - `DamnedLies <https://wiki.gnome.org/DamnedLies>`_
        - `Transifex <https://www.transifex.com/>`_
        - `Zanata <http://zanata.org/>`_
    - Upstream Repository (Done)
        - `git <https://git-scm.com/>`_

- Transtats Jobs
    - YML Based Jobs
        - Parser & ActionMapper (Done)
    - Streamline Jobs by Templates (Done)
    - Locate String Breakage (Done)

- Translation Status of Packages, sync with:
    - Build System (Done)
        - `koji <https://koji.fedoraproject.org/koji/>`_

- Transtats Engagements

    - Interactions
        - Dashboard: Integration of `PatternFly <https://www.patternfly.org/>`_ UI (Done)
        - Better stats representation in (**In Progress**)
            - Release, Package and Job Details
        - Use-case based UI designs
        - More sub-commands and flags in CLI

    - Flexibility
        - Scheduling of Jobs as per Release Schedule
            - to enable schedule based auto-sync
        - Emails about push/pull or translation status/diff

- Expanding Support
    - Translation Platform
        - `Weblate <https://weblate.org>`_
        - `Pootle <https://pootle.translatehouse.org/>`_
    - Translation File Format *in Jobs*
        - Java files (``properties``, ``dtd``)
        - PHP, JS (``ini``, ``json``)
    - More YML Job Templates
