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


Transtats 0.8.9
---------------

| Target delivery: End of June 2023


ToDo List
=========

- New Feature, Bug fix, Enhancement
    - Provision for package sets.
    - Search a job log.
    - Translation snapshots.
    - Handle translation files in multiple tarballs.

- Technical Tasks
    - Error handling, improve test coverage.
    - Simultaneous jobs run (and multi-threading).
    - Prepare deployment for OpenShift 4.
        - Move from docker to buildah, single container to a pod.
    - Find an alternative of vagrant in dev env.
        - docker-compose may be.

- Expanding Support
    - Translation File Format *in Jobs*
        - Java files (``properties``, ``dtd``)
        - PHP, JS (``ini``, ``json``, ``js``)
    - More YAML Job Template Implementations

- Automation
    - Batch processing of pipeline actions.
    - Scheduling jobs based on release dates.
    - Scheduling of pipeline configurations.

- User Personalization
    - Expand Authentication Methods: SAML, Social.
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
