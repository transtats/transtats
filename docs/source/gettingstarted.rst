===============
Getting Started
===============

Introduction
============

Reports are generated for the languages, and their aliases are used while syncing. One can create a language set, which can be associated with a product release. Multiple instances of a translation platform can be added. A release should have a language set and a schedule attached. Transtats jobs talk to upstream repositories, translation platforms and build systems to keep translation statistics, build tags and release schedule latest.

Add and Configure Packages
==========================

While adding a package, upstream URL is required. And the package name is verified with selected translation platform. Translation of a package can be tracked for multiple products. The package should be sync'd with the translation platform and the build system. Once sync'd, branch mapping will be created. It maps product releases with most suitable project versions available at translation platform and with appropriate build tags. The package can be sync'd with upstream repo as well.

Generate Diff
=============

Once we have all versions/tags mentioned in branch mapping of the package sync'd with pointing translation platform or build system, differences can be created. This answers - for a package - latest translations are packaged or not? Which languages need attention?

Add Coverage Rule
=================

Coverage (for a group of packages in a set of languages to a given release) is based on rules. Slug form of the rule name will be saved. This should be specific for a product release. Packages having branch mapping are included here. Languages can be picked either from language set associated with the release or from enabled ones. Corresponding build tags can be overridden too. This shows statistics differences in details.

Translation Status
==================

Summary and Details
    Transtats has two traversal options: releases and languages. One can see high level summary and can pick any of releases or languages, followed by packages. Summary can tell you: packages which are out of sync, release by release l10n effort progress and much more. Run a job to track string change.
