========
Overview
========

Configuration
-------------

1. Inventory
    Languages & their sets, translation platforms and product releases are grouped as inventory. One product can have multiple releases. Like, Fedora and Fedora 34, Fedora 35 are releases. Sample data contains some of them. Inventory are basis to releases, packages, jobs and graph rules. And hence probably the first thing to look at.

2. Releases
    A particular release which has a schedule and information regarding *in how many languages it will be available*. Releases are primary to branch mapping. A package associated with any of the product(s), automatically being tracked for all releases underneath. One release can be associated with one language set.

3. Packages
    Translation progress would be tracked for added packages. They should have upstream repository URL and translation platform project. A package can be linked with multiple products and should have a branch mapping. Once all versions / tags are sync'd with respective sources, translation differences could be generated. Packages should be sync'd at intervals.

Summary and Details
-------------------

1. Releases - Translation Progress
    Translation update volume estimation for a product release at an early stage of a release cycle. It has three views: combined, detailed and language-wise. Combined will sum up translated and untranslated for all languages for a package. Detailed contains language wise %age representation. Language-wise shows overall picture as well as translated, untranslated statistics of every package for each language.

2. Packages - Translation Completeness
    Translation progress, gaps, errors of a package by syncing with source repositories, translation platforms and build systems. Package needs to get sync'd with all three to fill statistics. Stats are represented in tabular and graph forms, per language also. This shows translation trends of last few releases. Summary highlights out-of-sync packages.

3. Insights - Translation Coverage
    Coverage of a group of packages for a specific release in associated or selected languages. These are based on graph rules. Packages must have branch mapping and respective sync done before they can participate in graph rule.

Workflow Automation
-------------------

1. Job templates
    Currently, seven templates are to choose from. They can be used as-is.

    ``syncupstream``, ``syncdownstream``, ``stringchange``, ``pushtrans``, ``dpushtrans``, ``pulltrans`` and ``pulltransmerge``

    - `syncupstream`
        clone package source repository, filter translation files and calculate statistics
    - `syncdownstream`
        locate latest built SRPM, unpacks, filter translation files and calculate statistics
    - `stringchange`
        clone package source repo, generates template (POT) as per given command, download respective template from platform and compare/find diff
    - `pushtrans`
        clone package source repository, filter translations and upload to the CI platform.
    - `dpushtrans`
        download translations from package translation platform and upload to the CI platform.
    - `pulltrans`
         download translations from CI platform and submit back.
    - `pulltransmerge`
         download translations from CI platform and creates merge request.


    Requires four values:
     - Package Name (*derived stats can be saved only if this is added already*)
     - Build System (*build system associated with the release*)
     - Build Tag (*run sync task for build tags to keep the dropdown updated*)
     - Release Slug (*find this on the release page, at tooltip or in URL*)
     - Pipeline UUID (*gets generated as soon as a pipeline is created*)

    **SyncDownstream**
    could be run for any package (also for those not added in Transtats) and for any build tag available. This makes the job really wonderful tool to inspect SRPM.

    Dry runs are also supported. Each YAML job has a unique URL to see details and share!

2. Tasks
    Functions which are basis to fetch some essential data
     - sync with translation platform for project details.
     - sync with release schedule to update calendar.
     - sync with build system for their latest build tags.
        *required for branch mapping (this is one of the first steps)*

    Logs are kept.
