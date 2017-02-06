[![Build Status](https://travis-ci.org/transtats/transtats.svg?branch=master)](https://travis-ci.org/transtats/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

### About

In a software release cycle, localisation steps like extracting or updating language resource, pushing them to translation platform, pulling and packaging translations, quality checks etc. seem necessary but sometimes they lack attention which results in delay. Transtats is an attempt to tie up loose ends and then, may be automate some of the steps. Concept is based on syncing with Translation Platform for statistics, comparing stats with Release Streams, managing translation differences, keep upstream updated and create notifications.


#### Purpose

To be catalyst in *localisation of applications* by tracking translation progress for release streams.


#### Big Picture

1. **Register Project** Developers writing some app got plans to release it with non-english support. And hence sign-ups with TS. Technotes:  `Python Social Auth`.

2. **Enable i18n** Once TS has projects with their source code, it can determine: the project has been i18n enabled or not. If not TS can determine i18n framework and provide info/details or patch enabling the same. And once i18n capabilities are determined, strings should be marked for translation, manually or with the help of i18n lint tools. Technotes: This should be `TS modules` based, `Notification`

3. **Push Template** If project has enough strings marked and linked with a translation platform plus have some plans for which languages, TS can extract language template and push for initial discussion/translation as well as instantiate their revision management. Technotes: `TS Jobs`, `Diff Mgmt` may be JSON based, `Notification`

4. **Release Mapping** Project translation plans are need to be mapped with release stream schedule to meet deadlines. TS would track translation progress for mapped release streams and for their branches respectively. Further TS would provide various views to generate statistics in. Technotes: `Calendar`, `Background Tasks`, `Notifications`, `Graphs Rules`

5. **Pull Translation** Translation completion events or calendar/cron could trigger jobs to pull translations for set languages. i18n checks like PO filter, fonts etc. should be applied on pulled stuff and if passed TS may request a merge in project source tree. Technotes: `TS Jobs`, tests can be `TS modules` based, `Notification`

6. **Package Validation** To ensure packaging with planned language resources, TS keeps an eye on builds at release streams. Plus TS looks for storage of language artifacts in packaging format. Technotes:    `TS Jobs`, storage may be `TS Modules` based, `Notification`



### Get Involved

#### Setup development environment: virtualenv

Setup Virtualenvwrapper and PostgreSQL 9.5. Create virtualenv. Clone repo.

```shell
workon transtats
cd /path/to/transtats/repo
make devel
```

Copy `keys.json.example` to `keys.json` and put your values.

```shell
make migrations
make migrate
make run
```

#### Contribution

* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a [github issue](https://github.com/transtats/transtats/issues/new).
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses [travis](https://travis-ci.org/transtats/transtats) for tests.
* Join the #fedora-g11n channel on irc.freenode.net.



### Roadmap

As the project evolves, a roadmap will be published for each major release. Comments, suggestions, and requests to the current roadmap are welcome. Our goal in publishing a roadmap is transparency and community inclusion. A roadmap is the team's best guess based on experience, community requests, and feedback.

#### Transtats 0.1.0

We are currently working on `0.1.0` release.

Target delivery: Mid February 2017

* Enable admin to manage inventory
* Bring release branches into custom graphs
* Check stats with release streams source package
* Implement django celery beat for TS Jobs
* Unit tests and code cleanup & coverage
* Project docs and other stuffs



### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
