================
Transtats Server
================

Summary and Details
-------------------

1. Releases - Translation Status
    Translation update volume estimation for a product release at an early stage of a release cycle. It has three views: combined, detailed and language-wise. Combined will sum up translated and untranslated for all languages for a package. Detailed contains language wise %age representation. Language-wise shows overall picture as well as translated, untranslated statistics of every package for each language.

2. Packages - Translation Completeness
    Translation progress, gaps, errors of a package by syncing with source repositories, translation platforms and build systems. Package needs to get sync'd with all three to fill statistics. Stats are represented in tabular and graph forms, per language also. This shows translation trends of last few releases. Summary highlights out-of-sync packages.

3. Translation Coverage
    Coverage of a group of packages for a specific release in associated or selected languages. These are based on graph rules. Packages must have branch mapping and respective sync done before they can participate in graph rule.

Configuration
-------------

1. Inventory
    Languages & their sets, translation platforms and release streams are grouped as inventory. One release stream can have multiple release branches. Like, Fedora is a release stream and Fedora 28, Fedora 29 are release branches. Inventory could be managed through admin panel. Sample data contains some of them. Inventory are basis to release branches, packages, jobs and graph rules. And hence probably the first thing to look at.

2. Release Branch
    A particular release which has a schedule and information regarding *in how many languages it will be available*. Release branch are primary to branch mapping. A package associated with any of the release streams, automatically being tracked for all release branches underneath. One release branch can be associated with one language set.

3. Packages
    Translation progress would be tracked for added packages. They should have upstream repository URL and translation platform project URL. A package can be linked with multiple release streams and should have a branch mapping. Once all versions / tags are sync'd with respective sources, differences could be generated. Packages should be sync'd at intervals.

Jobs
----

1. Predefined Jobs
    Functions which are basis to fetch some essential data
     - sync with translation platform for projects
     - sync with release schedule to update calendar
     - sync with build system for build tags
        *required for branch mapping (this is one of the first steps)*

    Logs are kept.

2. YAML Based Jobs
    Currently, three templates are to choose from. They can be used as-is.

    ``syncupstream``, ``syncdownstream`` and ``stringchange``

    - `syncupstream`
        clone package source repository, filter translation files and calculate statistics
    - `syncdownstream`
        locate latest built SRPM, unpacks, filter translation files and calculate statistics
    - `stringchange`
        clone package source repo, generates template (POT) as per given command, download respective template from platform and compare/find diff

    Requires four values:
     - Package Name (*derived stats can be saved only if this is added already*)
     - Build System (*build system associated with added release stream*)
     - Build Tag (*To fill drop down with build tags, run sync job for build tags*)
     - Release Slug (*one can find this out on release page, at tooltip or in URL*)

    **SyncDownstream**
    could be run for any package (also for those not added in transtats) and for any build tag available. This makes the job really wonderful tool to inspect SRPM.

    Dry runs are also supported. Each YAML job has a unique URL to see details and share!
