=======
Roadmap
=======

| As the project evolves, a roadmap will be published for each major release. Comments, suggestions, and requests to the current roadmap are welcome. Our goal in publishing a roadmap is transparency and community inclusion.
| A roadmap is the team's best guess based on experience, community requests, and feedback.


Releases
========

| Please look `github releases <https://github.com/transtats/transtats/releases>`_ for details.
| See changelog `here <https://github.com/transtats/transtats/blob/devel/CHANGELOG.md>`_.


Upcoming Releases
*****************

| Versioning is mostly `MAJOR.MINOR.PATCH`
| And releases are scheduled every quarter end.

Transtats 0.8.0
---------------
| `<https://github.com/transtats/transtats/milestone/14>`_
| Target delivery: 18th Sept 2020


Transtats 0.8.5
---------------

| Target delivery: 18th Dec 2020


ToDo List
=========

- New Feature, Bug fix, Enhancement
    - Package name mapping.
    - Provision for package sets.
    - Search a job log.
    - Translation snapshots.
    - translate.f.o specific changes.
    - Translation files in multiple tarballs.
    - Additional upstream repository for `l10n`.

- Technical Tasks
    - Error handling, test cases.
    - Simultaneous jobs run (and multi-threading).
    - Prepare deployment for OpenShift 4.
        - Move from docker to buildah, single container to a pod.
    - Find an alternative of vagrant in dev env.

- Expanding Support
    - Translation File Format *in Jobs*
        - Java files (``properties``, ``dtd``)
        - PHP, JS (``ini``, ``json``, ``js``)
    - More YAML Job Template Implementations
        - ``verifytrans``

- Automation
    - Scheduling jobs based on release dates

- User Personalization
    - Multiple Authentication: FAS, SAML, Social.
    - Bootstrap Transtats for different tenants.
    - API sync for package, language-group ownerships.
    - User panel to configure package and other settings.
    - Customization of interfaces as per logged in user.
    - Notifications to package and/or language maintainers.

- Integration
    - Fedora Apps, Internal tools
    - Bugzilla, JIRA, IRC bot

- Documentation
    - Use cases (``docs``, ``blog``, ``transtats.org``)
    - User guide (``pdf``, ``screencast``)
    - Release notes, developers manual

| For complete list please browse `github issues <https://github.com/transtats/transtats/issues>`_.
