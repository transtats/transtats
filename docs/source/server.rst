================
Transtats Server
================

`transtats <https://github.com/transtats/transtats>`_ is a django application with postgres backend.

Releases
--------

Transtats can have one or multiple product(s) in one instance. And each Product can have multiple releases.
Staff role can manage products and releases. Adding a release has following fields:

``Release Branch Name`` Product release name with version. for example: Fedora 37

``Release Slug`` Transtats will formulate slug.
*And this slug will be validated with iCal retrieved from URL.* for example: fedora-37

``Current Phase`` Phase in which this release is running. for example: Development

``Language Set`` Language set which should be associated with this release.
*This is useful when we need to track a release for custom set of languages.*

``iCal URL`` Release schedule calendar URL. To fetch release milestone and dates.

``SCM Branch`` (optional) Release Build System Default Tag. for example: f37

``Enable flags`` Track Translation will enable translation tracking for this release.


Languages
---------

Languages are the backbone of translations tracking and other operations. Adding a language has following fields:

``Language Name`` Name of the language. for example: Japanese

``Locale ID`` Locale in the form of LANG_TERRITORY. for example: ja_JP

``Locale Script`` Script the language is based upon. for example: Hani

``Locale Alias`` (optional) for example: zh-Hans can be an alias for zh_CN locale.


Platforms
---------

In Transtats, Platform refers to a translation platform. for example Damned Lies, Phrase, Transifex, Weblate, Zanata, etc.
Adding a Platform has following fields:

``Platform Engine`` (dropdown) Platform engine helps system to determine specific tasks. for example: WEBLATE

``Platform Subject`` for example: Fedora

``Server URL`` for example: https://translate.fedoraproject.org

``Platform SLUG`` (dropdown) for example: WLTEFED refers to Weblate Fedora instance

``Enable/Disable`` To enable platform for sync operations.

``Server URL`` for example: https://translate.fedoraproject.org

``Auth User`` Username for API auth purposes.

``Auth Password/Token`` Password or Token for API auth purposes.

``CI Enable/Disable`` To enable platform for CI Pipeline operations.


Packages
--------

An authenticated user can create and manage a package. (a project in Transtats)
Adding a Package has following fields:

``Package Name`` Package id as-in translation platform. *Existence is validated with the translation platform.*

``Upstream URL`` Source repository location (Bitbucket, GitHub, Pagure etc).

``Upstream Localization URL`` (optional) Source repository location with translation resources.

``Translation Format`` (radio) File format translations are stored in the project.

``Translation Platform`` (dropdown) Translation statistics will be fetched from this server.

``Products`` (check) Translation progress for selected products will be tracked.
