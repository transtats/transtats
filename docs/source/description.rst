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

Settings
--------

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

Client
======

`transtats-cli <https://github.com/transtats/transtats-cli>`_ is a command line interface to query transtats server.

- **Usage**

    ::

        $ transtats [OPTIONS] COMMAND [ARGS]...

- **Options**

    --help
        Show help message and exit.

- **Commands**

    1. coverage
        Translation coverage as per graph rule.

    2. status
        Translation status of a package.

    3. version
        Display the current version.

    4. workload
        Translation workload of a release branch.
