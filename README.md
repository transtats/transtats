[![Build Status](https://travis-ci.org/sundeep-co-in/transtats.svg?branch=master)](https://travis-ci.org/sundeep-co-in/transtats)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

Tracking translation progress of the package for downstream releases with respect to current development.

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

Feel free to submit feature requests and/or bug fixes. Transtats uses [travis](https://travis-ci.org/sundeep-co-in/transtats) and [waffle](https://waffle.io/sundeep-co-in/transtats).


#### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
