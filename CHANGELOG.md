##### Fri Aug 04 2017 Sundeep Anand <suanand@redhat.com>
* Update Dockerfile and add Vagrant + Ansible playbook
* translation platforms auth settings for API
* package upstream sync for translation stats
* add unit tests & configure travis and logging
* add docker file, based on `fedora:latest`

##### Wed Apr 26 2017 Sundeep Anand <suanand@redhat.com> - release_0.1.1
* add combined lang view to translation workload
* add detailed stats view to workload estimation
* translation workload estimation per release branch
* add tabular view to translation status
* split package-refresh into sync and map branches
* add language-wise status graph for a package

##### Fri Mar 17 2017 Sundeep Anand <suanand@redhat.com> - release_0.1.0
* enable branch mapping for translation coverage
* provision section for package configurations
* implement language set and branch mapping features
* add django rest framework to ping server
* enable django admin to manage inventory and jobs

##### Mon Dec 05 2016 Sundeep Anand <suanand@redhat.com> - Concept
* enable ical sync for RHEL and Fedora - syncCalendar Jobs
* add and list graph rules, display graphs based on rules
* add release_stream_branches model, view, html, form
* settings summary and add stats templates dir
* package-names mapping provision
* move to Django ORM - migrations

##### Thu Sept 15 2016 Sundeep Anand <suanand@redhat.com> - Prototype
* add Transifex support - transplatform API configs
* enable displaying some charts based on sync'd data
* add logs settings page, add package transplatform validation
* enable transplatform projects and stats sync (zanata)
* add django-crispy-forms and enable add packages
* moved to Apache Licence Version 2.0
* add languages, transplatform, relstreams settings pages
* rename project to transtats, fix ui and migrate to PostgreSQL
* add features page, zanata api, view, manager and model
* initial structure with django: settings, requires, docs
