[![Website](https://img.shields.io/badge/website-transtats.org-orange.svg)](http://transtats.org)
[![CircleCI](https://circleci.com/gh/transtats/transtats/tree/devel.svg?style=svg)](https://circleci.com/gh/transtats/transtats/tree/devel)
[![Documentation Status](https://readthedocs.org/projects/transtats/badge/?version=latest)](http://transtats.readthedocs.io/en/latest/?badge=latest)

## Transtats

Transtats helps make packages ready to ship with translation completeness.

Use Cases
 - Tracking translation progress across packages for downstream releases with respect to current development.
 - Finding translation gaps by syncing with source repositories, translation platforms and build systems. To find out:
    - Is everything translated packaged and built?
    - Are all strings pushed to translation platform latest to software repositories?
 - At-a-glance picture for managing the l10n effort progress, release by release. And it's readiness.

To learn more about using Transtats, please point your browser to [docs](http://docs.transtats.org).

### Quick Start

Get docker daemon running. Pull `transtats` image *([docker.io](https://hub.docker.com/r/transtats/transtats/))* and get started.

- Pull the image *(No need to pull, if you have built the image)*
  ```shell
  $ sudo docker pull docker.io/transtats/transtats
  ```

- Run the image
  ```shell
  $ sudo docker run -d --name container_name -p 8080:8015 transtats/transtats
  ```

- Application should be accessible at `localhost:8080`.


### Get Involved

- Follow [contributing guide](./CONTRIBUTING.md) to get started developing, testing, and building Transtats Server.
- Join the `#transtats` channel on chat.freenode.net
- Open an [Issue](https://github.com/transtats/transtats/issues) to discuss new feature or a bug fix!

### License

[Apache License](http://www.apache.org/licenses/LICENSE-2.0), Version 2.0
