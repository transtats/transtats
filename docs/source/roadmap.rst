=======
Roadmap
=======

As the project evolves, a roadmap will be published for each major release. Comments, suggestions, and requests to the current roadmap are welcome. Our goal in publishing a roadmap is transparency and community inclusion. A roadmap is the team's best guess based on experience, community requests, and feedback.

Transtats 0.1.7
===============

| We are currently working on :code:`0.1.7` release.
| :code:`0.1.7-rc.1` Integration of PatternFLY UI.

Target delivery: By mid of March 2019

Backlog is `here <https://github.com/transtats/transtats/issues>`_. For release features list please look at `milestone <https://github.com/transtats/transtats/milestone/10>`_.

To Do
=====

- Manage Inventory
    - Languages and their Sets (Done)
    - Translation Platforms (Done)
    - Product and their Releases (Done)

- Translation Status of Packages, sync with:
    - Translation Platform (Done)
        - DamnedLies
        - Transifex
        - Zanata
    - Upstream Repository (Done)
        - git
    - Build System (Done)
        - koji

- Transtats Jobs
    - YML Based Jobs
        - Parser & ActionMapper (Done)
    - Streamline Jobs by Templates (Done)
    - Locate String Breakage (Done)

- Transtats Engagements

    - Interactions
        - Dashboard: Integration of new PatternFly UI (**In Progress**)
        - Better stats representation
            - Release, Package and Job Details Page
        - More sub-commands and flags in CLI

    - Flexibility
        - Scheduling of Jobs as per Release Schedule
            - to enable schedule based auto-sync
        - Emails about push/pull or translation status/diff

- Expanding Support
    - Translation Platform
        - Weblate
    - Translation File Format in Jobs
        - Java files (``properties``, ``dtd``)
    - More YML Job Templates
