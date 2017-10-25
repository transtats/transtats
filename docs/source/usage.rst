=====
Usage
=====

Check Inventory
===============

Graphs will be generated for enabled languages, aliases are used while syncing. One can create a language set, which can be associated with a release branch. Multiple instances of a translation platform can be added. RHEL and Fedora are release streams whereas RHEL 7.4 is a branch. A release branch should have a language set and a schedule. Transtats jobs sync at intervals to keep stats and schedule latest.

Add and Configure Packages
==========================

While adding a package, upstream URL is required. And package name is verified with selected translation platform. Translation of a package can be tracked for multiple release streams. Package can be sync'd with translation platform while adding itself. Once sync'd, branch mapping can be created. It maps Transtats release branches with most suitable project versions available at translation platform. Package can be sync'd with upstream repo as well (limited to git repo and PO files).

Add Graph Rule
==============

Slug form of rule name would be saved. This should be specific for a release branch. Packages having branch mapping created can only be included here. Languages could be picked from language set associated with the release branch or from enabled ones. Somehow if a package is not tracked for a release stream and selected for inclusion Transtats would show an error.

Graphs
======

Transtats has two graph views: specific to a package in all languages for all branches and another specific to a release branch in chosen languages for selected packages. Latter is a graph rule representation and its accuracy depends on branch mapping of packages. A sync'd package can appear in former view whereas branch mapping is necessary for latter. Even translation workload could be estimated for a release branch. This has three views: combined, detailed and per languages.
