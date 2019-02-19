## Deploying Transtats on OpenShift

This directory contains files required to deploy Transtats on [OpenShift](https://www.openshift.org/) cluster.

## How to run it locally?

- Install PostgreSQL Server and make it accessible over FQDN.
- Install [minishift](https://github.com/minishift/minishift)
- Modify the `database-host` in `secret.yml` which should point to PostgreSQL host.
- Run the following commands after you login to your cluster on terminal

  ```sh
  $ oc new-project transtats
  $ oc create -f deploy/openshift
  $ oc start-build transtats-build
  ```

Once build/deploy finishes, application shall be accessible.
