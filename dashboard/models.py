# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# python
from uuid import uuid4

# django
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models


TABLE_PREFIX = 'ts_'


class Languages(models.Model):
    """
    Languages Model
    """
    locale_id = models.CharField(
        max_length=50, primary_key=True, verbose_name="Locale ID"
    )
    lang_name = models.CharField(
        max_length=400, unique=True, verbose_name="Language Name"
    )
    locale_alias = models.CharField(
        max_length=50, null=True, verbose_name="Locale Alias"
    )
    lang_status = models.BooleanField(verbose_name="Enable/Disable")

    def __str__(self):
        return self.lang_name

    class Meta:
        db_table = TABLE_PREFIX + 'locales'
        verbose_name = "Language"


class LanguageSet(models.Model):
    """
    Language Set Model
    """
    lang_set_id = models.AutoField(primary_key=True)
    lang_set_name = models.CharField(
        max_length=1000, verbose_name="Language Set Name"
    )
    lang_set_slug = models.CharField(
        max_length=400, unique=True, verbose_name="Language Set SLUG"
    )
    lang_set_color = models.CharField(
        max_length=100, unique=True, verbose_name="Tag Colour"
    )
    locale_ids = ArrayField(
        models.CharField(max_length=50, blank=True),
        default=list, null=True, verbose_name="Locale IDs"
    )

    def __str__(self):
        return self.lang_set_name

    class Meta:
        db_table = TABLE_PREFIX + 'langset'
        verbose_name = "Language Set"


class TransPlatform(models.Model):
    """
    Translation Platforms Model
    """
    platform_id = models.AutoField(primary_key=True)
    engine_name = models.CharField(
        max_length=200, verbose_name="Platform Engine"
    )
    subject = models.CharField(
        max_length=200, null=True, verbose_name="Platform Subject"
    )
    api_url = models.URLField(max_length=500, unique=True, verbose_name="Server URL")
    platform_slug = models.CharField(
        max_length=400, unique=True, verbose_name="Platform SLUG"
    )
    server_status = models.BooleanField(verbose_name="Enable/Disable")
    projects_json = JSONField(null=True)
    projects_lastupdated = models.DateTimeField(null=True)

    def __str__(self):
        return "{0} {1}".format(self.engine_name, self.subject)

    class Meta:
        db_table = TABLE_PREFIX + 'transplatforms'
        verbose_name = "Translation Platform"


class ReleaseStream(models.Model):
    """
    Release Stream Model
    """
    relstream_id = models.AutoField(primary_key=True)
    relstream_name = models.CharField(
        max_length=200, verbose_name="Release Stream Name"
    )
    relstream_slug = models.CharField(
        max_length=400, unique=True, verbose_name="Release Stream SLUG"
    )
    relstream_server = models.URLField(
        max_length=500, unique=True, verbose_name="Release Stream Server"
    )
    relstream_built = models.CharField(
        max_length=200, null=True, verbose_name="Release Build System"
    )
    srcpkg_format = models.CharField(
        max_length=50, null=True, verbose_name="Source Package Format"
    )
    top_url = models.URLField(max_length=500, unique=True, verbose_name="Top URL")
    web_url = models.URLField(max_length=500, unique=True, null=True, verbose_name="Web URL")
    krb_service = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Kerberos Service"
    )
    auth_type = models.CharField(max_length=200, null=True, blank=True, verbose_name="Auth Type")
    amqp_server = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="AMQP Server"
    )
    msgbus_exchange = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Message Bus Exchange"
    )
    major_milestones = ArrayField(
        models.CharField(max_length=1000, blank=True),
        default=list, null=True, verbose_name="Major Milestones"
    )
    relstream_phases = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=list, null=True, verbose_name="Release Stream Phases"
    )
    relstream_status = models.BooleanField(verbose_name="Enable/Disable")

    def __str__(self):
        return self.relstream_name

    class Meta:
        db_table = TABLE_PREFIX + 'relstreams'
        verbose_name = "Release Stream"


class StreamBranches(models.Model):
    """
    Stream Branches Model
    """
    relbranch_id = models.AutoField(primary_key=True)
    relbranch_name = models.CharField(max_length=500, verbose_name="Release Branch Name")
    relbranch_slug = models.CharField(max_length=500, unique=True, verbose_name="Release Branch Slug")
    relstream_slug = models.CharField(max_length=400, verbose_name="Release Stream Slug")
    lang_set = models.CharField(max_length=200, verbose_name="Language Set")
    scm_branch = models.CharField(max_length=100, null=True, blank=True, verbose_name="SCM Branch Name")
    created_on = models.DateTimeField()
    current_phase = models.CharField(max_length=200, null=True, verbose_name="Current Phase")
    calendar_url = models.URLField(max_length=500, null=True, verbose_name="Calender iCal URL")
    schedule_json = JSONField(null=True)
    sync_calendar = models.BooleanField(default=True, verbose_name="Sync Calender")
    notifications_flag = models.BooleanField(default=True, verbose_name="Notification")
    track_trans_flag = models.BooleanField(default=True, verbose_name="Track Translation")

    def __str__(self):
        return self.relbranch_name

    class Meta:
        db_table = TABLE_PREFIX + 'relbranches'
        verbose_name_plural = "Release Branches"


class Packages(models.Model):
    """
    Packages Model
    """
    package_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=1000, unique=True, verbose_name="Package Name")
    upstream_name = models.CharField(max_length=1000, null=True, verbose_name="Upstream Name")
    upstream_url = models.URLField(max_length=2000, unique=True, verbose_name="Upstream URL")
    transplatform_slug = models.ForeignKey(
        TransPlatform, on_delete=models.CASCADE,
        to_field='platform_slug', verbose_name="Translation Platform"
    )
    transplatform_name = models.CharField(max_length=1000, null=True,
                                          verbose_name="Package Name at Translation Platform")
    # translation platform project http url
    transplatform_url = models.URLField(max_length=500,
                                        verbose_name="Translation Platform Project URL")
    release_streams = ArrayField(
        models.CharField(max_length=400, blank=True),
        default=list, null=True, verbose_name="Release Streams"
    )
    package_details_json = JSONField(null=True)
    details_json_lastupdated = models.DateTimeField(null=True)
    package_name_mapping = JSONField(null=True)
    release_branch_mapping = JSONField(null=True, blank=True)
    mapping_lastupdated = models.DateTimeField(null=True)
    transtats_lastupdated = models.DateTimeField(null=True)

    def __str__(self):
        return self.package_name

    class Meta:
        db_table = TABLE_PREFIX + 'packages'
        verbose_name = "Package"


class Jobs(models.Model):
    """
    Jobs Model
    """
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.UUIDField(default=uuid4, editable=False)
    job_type = models.CharField(max_length=200)
    job_start_time = models.DateTimeField()
    job_end_time = models.DateTimeField(null=True)
    job_log_json = JSONField(null=True)
    job_result = models.NullBooleanField()
    job_remarks = models.CharField(max_length=200, null=True)

    @property
    def duration(self):
        timediff = self.job_end_time - self.job_start_time
        return timediff.total_seconds()

    class Meta:
        db_table = TABLE_PREFIX + 'jobs'


class SyncStats(models.Model):
    """
    Sync Stats Model
    """
    sync_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=500)
    job_uuid = models.UUIDField()
    project_version = models.CharField(max_length=500, null=True)
    stats_raw_json = JSONField(null=True)
    sync_iter_count = models.IntegerField()
    sync_visibility = models.BooleanField()

    class Meta:
        db_table = TABLE_PREFIX + 'syncstats'


class GraphRules(models.Model):
    """
    Graph Rules Model
    """
    graph_rule_id = models.AutoField(primary_key=True)
    rule_name = models.CharField(max_length=1000, unique=True)
    rule_packages = ArrayField(
        models.CharField(max_length=1000, blank=True), default=list
    )
    rule_langs = ArrayField(
        models.CharField(max_length=400, blank=True), default=list
    )
    rule_relbranch = models.CharField(max_length=500)
    created_on = models.DateTimeField()
    rule_status = models.BooleanField()

    class Meta:
        db_table = TABLE_PREFIX + 'graphrules'
