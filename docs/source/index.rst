.. raw:: html

    <a href="http://transtats.org" target="_blank"><img src="https://img.shields.io/badge/website-transtats.org-orange.svg" alt="website"></a>
    <a href="https://circleci.com/gh/transtats/transtats" target="_blank"><img src="https://circleci.com/gh/transtats/transtats.svg?style=svg" alt="Build Status"></a>
    <a href="https://github.com/transtats/transtats/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/transtats/transtats.svg?style=social&label=Stars" alt="Stars"></a>
    <br><br>

=========
Transtats
=========

*Track Translation Completeness.*

In a software release cycle, some of the necessary localization steps lack attention which affect translation quality and delivery. These steps (for a package) are extracting or updating language resource, pushing that to translation platform, pulling and packaging translations, quality checks etc. Transtats helps to tie up loose ends and make packages ready to ship with translation completeness. Further, its an attempt to bring automation in ``i18n`` ``l10n`` space through jobs.

Transtats Server is a simple django application with PostgreSQL backend. Has one CLI and some ansible playbooks for deployment. And, can be deployed on container based systems.

.. toctree::
    :caption: Table of Contents
    :maxdepth: 2

    server
    api
    client
    gettingstarted
    getinvolved
    roadmap
    releases
    license
