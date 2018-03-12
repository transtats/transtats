.. raw:: html

    <a href="http://transtats.org" target="_blank"><img src="https://img.shields.io/badge/website-transtats.org-orange.svg" alt="website"></a>
    <a href="https://circleci.com/gh/transtats/transtats" target="_blank"><img src="https://circleci.com/gh/transtats/transtats.svg?style=svg" alt="Build Status"></a>
    <a href="https://github.com/transtats/transtats/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/transtats/transtats.svg?style=social&label=Stars" alt="Stars"></a>
    <br><br>

=========
Transtats
=========

In a software release cycle, localisation steps like extracting or updating language resource, pushing them to translation platform, pulling and packaging translations, quality checks etc. seem necessary but sometimes they lack attention which results in delay. Transtats is an attempt to tie up loose ends and then, may be automate some of the steps. Concept is based on syncing with Upstream Repository, Translation Platform and Build System for statistics and translation resources, comparing stats based on mapping, calculating translation differences, keep upstream updated and create notifications.

Stack
-----

Transtats Server is a simple django application with PostgreSQL backend. Has one CLI and some ansible playbooks for deployment.

.. toctree::
    :caption: Table of Contents
    :maxdepth: 2

    server
    client
    gettingstarted
    getinvolved
    roadmap
    releases
    license
