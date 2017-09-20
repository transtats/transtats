[![Build Status](https://travis-ci.org/transtats/transtats.svg?branch=master)](https://travis-ci.org/transtats/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

### About

In a software release cycle, localisation steps like extracting or updating language resource, pushing them to translation platform, pulling and packaging translations, quality checks etc. seem necessary but sometimes they lack attention which results in delay. Transtats is an attempt to tie up loose ends and then, may be automate some of the steps. Concept is based on syncing with Translation Platform for statistics, comparing stats with Release Streams, managing translation differences, keep upstream updated and create notifications.


#### Purpose

To be a catalyst in *localisation of applications* by creating mapping between upstream, translation platform and release streams.

#### App Description

##### Graphs

1. **Translation Status** Translation progress of a package for most of the branches in all enabled languages.

2. **Translation Coverage** Coverage of a package list for a specific release in associated or selected languages.

3. **Translation Workload** Translation workload estimation for a release branch across packages.

##### Settings

1. **Inventory** Languages & their sets, translation platforms and release streams with their branches are grouped as inventory. Plus upstream.

2. **Release Branch** A particular release which has a schedule and information regarding *in how many languages it will be available*. 

3. **Packages** Translation progress would be tracked for added packages. They should have upstream repository URL and translation platform project URL. A package can be linked with multiple release streams and should have a branch mapping.

4. **Jobs** Some functions which are planned to be automated like sync with translation repositories, update release schedule etc. Logs are kept.

5. **Graph Rules** Rules to track translation *as in* coverage of a package list for a specific release branch in a set of languages.

#### Releases

Please look [here](https://github.com/transtats/transtats/releases) for release details.



### Get Involved

Pull code `$ git clone https://github.com/transtats/transtats.git`

Install ansible, docker and vagrant.

```shell
$ sudo vagrant up
$ sudo vagrant ssh
```

This will setup devel env and run container plus, `ssh` into it.

Run application

```shell
$ cd /workspace
$ make run
hit localhost:8080 in browser
```

Create migrations `make migrations`

Run tests `make lint test` 

Generate docs `make docs`

#### Contribution

* The *devel* branch is the release actively under development.
* The *master* branch corresponds to the latest stable release.
* If you find any bug/issue or got an idea, open a [github issue](https://github.com/transtats/transtats/issues/new).
* Feel free to submit feature requests and/or bug fixes on *devel* branch.
* Transtats uses [travis](https://travis-ci.org/transtats/transtats) for tests.



### Roadmap

As the project evolves, a roadmap will be published for each major release. Comments, suggestions, and requests to the current roadmap are welcome. Our goal in publishing a roadmap is transparency and community inclusion. A roadmap is the team's best guess based on experience, community requests, and feedback.

#### Transtats 0.1.4

We are currently working on `0.1.4` release.

Target delivery: Mid of October 2017

For features list please look [here](https://github.com/transtats/transtats/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_0.1.4).

### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
