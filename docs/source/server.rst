================
Transtats Server
================

Summary and Details
-------------------

1. Translation Status - Releases
    Translation workload estimation for a release branch across packages. It has three views: combined, detailed and language-wise. Combined will sum up translated and untranslated for all languages for a package. Detailed contains language wise %age representation. Language-wise shows translated and untranslated stats of a package for each language.

2. Translation Status - Packages
    Translation progress of a package for sync'd branches in all enabled languages. Package needs to get sync'd with Upstream Repository, Translation Platform and Build System to fill statistics. Stats are represented in tabular and graph forms, per language also. This shows translation treads of last few releases. Summary highlights out-of-sync packages.

3. Translation Coverage
    Coverage of a group of packages for a specific release in associated or selected languages. These are based on graph rules. Packages must have branch mapping and respective sync done before they can participate in graph rule.

Configuration
-------------

1. Inventory
    Languages & their sets, translation platforms and release streams are grouped as inventory. One release stream can have multiple release branches. Like, Fedora is a release stream and Fedora 28, Fedora 29 are release branches. Inventory could be managed through admin panel. Demo data contains some of them. Inventory are basis to release branches, packages, jobs and graph rules. And hence probably the first thing to look at.

2. Release Branch
    A particular release which has a schedule and information regarding *in how many languages it will be available*. Release branch are primary to branch mapping. A package associated with any of the release streams, automatically being tracked for all release branches underneath. One release branch can be associated with one language set.

3. Packages
    Translation progress would be tracked for added packages. They should have upstream repository URL and translation platform project URL. A package can be linked with multiple release streams and should have a branch mapping. Once all versions / tags are sync'd with respective sources, differences could be generated. Packages should be sync'd at intervals.

Jobs
----

1. Sync Jobs
    Functions which are planned to be automated like
     - sync with translation platform for translation stats
     - sync with upstream repositories for translation resources
     - sync with release schedule to update calendar
     - sync with build system for build tags
        *required for branch mapping (this is one of the first steps)*

    Logs are kept.

2. YAML Based Jobs
    Currently, this is to talk with build system. The YAML template can be used as-is.

    This requires three values:
     - Package Name (*derived stats can be saved only if this is added already*)
     - Build System (*build system associated with added release stream*)
     - Build Tag (*To fill dropdown with build tags, run sync job for build tags*)

    Once started it locates latest build, get SRPM and extract, apply patches, filter translation resources and calculates stats. Job could be run for any tag. Dry runs are also supported.
