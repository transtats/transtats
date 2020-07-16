[![Website](https://img.shields.io/badge/website-transtats.org-orange.svg)](http://transtats.org)
[![CircleCI](https://circleci.com/gh/transtats/transtats/tree/devel.svg?style=svg)](https://circleci.com/gh/transtats/transtats/tree/devel)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

**Overview and trends for language translations across releases**

[transtats.org](http://transtats.org/)

Transtats web interface helps make packages ready to ship with translation completeness. It seems meaningful to localization teams, package maintainers, developers and quality engineers.

##### Use Cases
 - Tracking translation progress across packages for product releases with respect to their current development.
 - Finding translation gaps by syncing with source repositories, translation platforms and build systems. To find out:
    - Is everything translated, packaged and built?
    - Which packages are out-of-sync and for which language(s)?
    - Are all strings pushed to translation platform latest to source repositories?
 - At-a-glance picture for managing the localization effort progress, release by release. And it's readiness.

To learn about using Transtats, please point your browser to [docs](http://docs.transtats.org).

### Quick Start

Get docker daemon running. Pull `transtats` image *(from [docker.io](https://hub.docker.com/r/transtats/transtats/))* and get started.

- Pull the image *(or build your own)*
  ```shell
  $ sudo docker pull docker.io/transtats/transtats
  ```

- Run the image
  ```shell
  $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats
  ```

- Application should be accessible at `localhost:8080`.


### Learning More

This project has been covered at a number of places:

- [Tracking Translations with Transtats](https://fedoramagazine.org/tracking-translations-with-transtats/) in [Fedora Magazine](https://fedoramagazine.org/)
- [Use cases for Transtats in the Fedora community](https://www.youtube.com/watch?v=jgXJZRj43M0) at [Fedora Flock 2019](https://flock2019.sched.com/)
- [Introduction to Transtats](https://www.youtube.com/watch?v=8q9cg-wsrUg) at [FOSSASIA 2018](https://2018.fossasia.org/)

### Get Involved

- Follow [contributing guide](./CONTRIBUTING.md) to make changes in Transtats.
- Join the `#transtats` channel on chat.freenode.net
- See [roadmap](http://docs.transtats.org/en/latest/roadmap.html). And open an [Issue](https://github.com/transtats/transtats/issues) to discuss new feature.
- Browse [issues](https://github.com/transtats/transtats/issues) and submit your `PR` for the bug fix!
- Read [Changelog](https://github.com/transtats/transtats/blob/master/CHANGELOG.md) and [Terms of Use](http://transtats.org/terms.html)

### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
