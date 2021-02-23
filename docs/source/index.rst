.. raw:: html

    <a href="http://transtats.org" target="_blank"><img src="https://img.shields.io/badge/website-transtats.org-orange.svg" alt="website"></a>
    <a href="https://circleci.com/gh/transtats/transtats" target="_blank"><img src="https://circleci.com/gh/transtats/transtats.svg?style=svg" alt="Build Status"></a>
    <a href="https://github.com/transtats/transtats/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/transtats/transtats.svg?style=social&label=Stars" alt="Stars"></a>
    <br><br>

=========
Transtats
=========

`transtats.org <http://transtats.org/>`_ - *overview and trends for language translations across releases.*

In a software release cycle, some of the necessary localization steps lack attention which affect translation quality and delivery. These steps (*for a package*) are extracting or updating language resource, pushing that to translation platform, pulling and packaging translations, quality checks etc. Transtats helps to tie up loose ends and make packages ready to ship with translation completeness. Furthermore, its an attempt to bring automation in ``i18n`` ``l10n`` space through jobs.

Transtats Server is a simple django application with PostgreSQL backend, which analyses and processes the translation data for meaningful representations. It has a CLI and some ansible playbooks for deployments. And, can be deployed on shared, dedicated or container based environments.

The ``Jobs framework`` is a centralized processor through which we can solve multiple sets of problems in a flexible way. Because, it has information about Product Release (*and its Schedule*), Package Source Repo, Package Translation Platform, and Package Build System; and interestingly we can expand the support. Multiple sets of problems can be captured and executed in the form of Job Templates. Moreover, as the jobs are YAML based, they're flexible - we can edit them.


Help
----

Join **#transtats** channel at freenode, write to transtats@redhat.com


.. toctree::
    :caption: Table of Contents
    :maxdepth: 2

    overview
    api
    client
    getinvolved
    roadmap
    license
