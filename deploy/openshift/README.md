## Deploying Transtats on OpenShift

This directory contains files required to deploy Transtats on OpenShift cluster.

## How to run it locally?

- You must have PostgreSQL installed somewhere which is accessible from your machine
- Install [minishift](https://github.com/minishift/minishift)
- Modify the `database-host` from `secret.yml` to point to your PostgreSQL instance
- Run the following commands once you login to your cluster from terminal

  ```sh
  $ oc new-project transtats-deployment
  $ oc create -f deploy/openshift
  $ oc start-build transtats-build
  ```
Once this finishes you will be able to access the application.

