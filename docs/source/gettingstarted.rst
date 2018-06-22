===============
Getting Started
===============

Check Inventory
===============

Graphs will be generated for enabled languages, aliases are used while syncing. One can create a language set, which can be associated with a release branch. Multiple instances of a translation platform can be added. A release branch (for example - Fedora 28) should have a language set and a schedule. Transtats jobs sync with upstream repository, translation platform and build system to keep stats, build tags and schedule latest.

Add and Configure Packages
==========================

While adding a package, upstream URL is required. And package name is verified with selected translation platform. Translation of a package can be tracked for multiple release streams. Package should be sync'd with translation platform and build system. Once sync'd, branch mapping can be created. It maps Transtats release branches with most suitable project versions available at translation platform and with appropriate build tags. Package can be sync'd with upstream repo as well.

Generate Diff
=============

Once we have all versions / tags mentioned in branch mapping of a package sync'd with either translation platform or build system, differences can be created and observed. This answers - for a package - latest translations are packaged or not? If not, is some patch applied at the last moment? Which languages need attention?

Add Graph Rule
==============

Translation coverages (translation status of a group of packages in a set of languages to a given release) are based on rules. Slug form of rule name would be saved. This should be specific for a release branch. Packages having branch mapping created can only be included here. Languages could be picked from language set associated with the release branch or from enabled ones. Somehow if a package is not tracked for a release stream and selected for inclusion Transtats would show an error.

Translation Status
==================

Summary and Details
    Transtats has two traversal options: releases and packages. One can see high level summary and can pick any one release or a package for details. Summary can tell you - packages which are out of sync, translation workload estimate for each language per release, and much more. Detailed views contain language wise stats, translation position etc. Another form is coverage, which depends on graph rules and branch mapping.
