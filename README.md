[![Website](https://img.shields.io/badge/website-transtats.org-orange.svg)](http://transtats.org)
[![CircleCI](https://circleci.com/gh/transtats/transtats/tree/devel.svg?style=svg)](https://circleci.com/gh/transtats/transtats/tree/devel)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

**Track translations and automate workflow.**

Transtats web interface helps developers to ship projects with translation completeness, localization managers to automate workflow and oversee the effort progress by product releases as well as language maintainers to estimate translation volume.

To learn about using Transtats, please point your browser to [docs](http://docs.transtats.org).

### Quick Start

Get docker daemon running. Build `transtats` image and get started.

- Build and run the image
  ```shell
  $ git clone https://github.com/transtats/transtats.git
  $ cd transtats
  $ sudo docker build -t transtats/transtats deploy/docker
  $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats
  ```

- Application should be accessible at `localhost:8080`.

### Get Involved

- Follow [contributing guide](./CONTRIBUTING.md) to make changes in Transtats.
- Join the `#transtats` channel on Libera.Chat
- See [roadmap](http://docs.transtats.org/en/latest/roadmap.html). And open an [issue](https://github.com/transtats/transtats/issues/new) to discuss new feature.
- Browse [issues](https://github.com/transtats/transtats/issues) and submit your `PR` for the bug fix!
- Read [Changelog](https://github.com/transtats/transtats/blob/master/CHANGELOG.md) and [Terms of Use](http://transtats.org/terms.html)

### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
