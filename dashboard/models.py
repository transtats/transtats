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
    locale_id = models.CharField(max_length=50, primary_key=True)
    lang_name = models.CharField(max_length=400, unique=True)
    locale_alias = models.CharField(max_length=50, null=True)
    lang_status = models.BooleanField()
    lang_set = models.CharField(max_length=200)

    class Meta:
        db_table = TABLE_PREFIX + 'locales'


class TransPlatform(models.Model):
    """
    Translation Platforms Model
    """
    platform_id = models.AutoField(primary_key=True)
    engine_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, null=True)
    api_url = models.URLField(max_length=500, unique=True)
    platform_slug = models.CharField(max_length=400, unique=True)
    server_status = models.BooleanField()
    projects_json = JSONField(null=True)
    projects_lastupdated = models.DateTimeField(null=True)

    class Meta:
        db_table = TABLE_PREFIX + 'transplatforms'


class ReleaseStream(models.Model):
    """
    Release Stream Model
    """
    relstream_id = models.AutoField(primary_key=True)
    relstream_name = models.CharField(max_length=200)
    relstream_slug = models.CharField(max_length=400, unique=True)
    relstream_server = models.URLField(max_length=500, unique=True)
    relstream_built = models.CharField(max_length=200, null=True)
    srcpkg_format = models.CharField(max_length=50, null=True)
    top_url = models.URLField(max_length=500, unique=True)
    web_url = models.URLField(max_length=500, unique=True, null=True)
    krb_service = models.CharField(max_length=200, null=True)
    auth_type = models.CharField(max_length=200, null=True)
    amqp_server = models.CharField(max_length=500, null=True)
    msgbus_exchange = models.CharField(max_length=200, null=True)
    major_milestones = ArrayField(
        models.CharField(max_length=1000, blank=True),
        default=list, null=True
    )
    relstream_phases = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=list, null=True
    )
    relstream_status = models.BooleanField()

    class Meta:
        db_table = TABLE_PREFIX + 'relstreams'


class StreamBranches(models.Model):
    """
    Stream Branches Model
    """
    relbranch_id = models.AutoField(primary_key=True)
    relbranch_name = models.CharField(max_length=500)
    relbranch_slug = models.CharField(max_length=500, unique=True)
    relstream_slug = models.CharField(max_length=400)
    scm_branch = models.CharField(max_length=100, null=True)
    created_on = models.DateTimeField()
    current_phase = models.CharField(max_length=200, null=True)
    calendar_url = models.URLField(max_length=500, unique=True, null=True)
    schedule_json = JSONField(null=True)
    sync_calendar = models.BooleanField(default=True)
    notifications_flag = models.BooleanField(default=True)
    track_trans_flag = models.BooleanField(default=True)

    class Meta:
        db_table = TABLE_PREFIX + 'relbranches'


class Packages(models.Model):
    """
    Packages Model
    """
    package_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=1000, unique=True)
    upstream_name = models.CharField(max_length=1000, null=True)
    upstream_url = models.URLField(max_length=2000, unique=True)
    transplatform_slug = models.ForeignKey(
        TransPlatform, on_delete=models.CASCADE,
        to_field='platform_slug'
    )
    transplatform_name = models.CharField(max_length=1000, null=True)
    # translation platform project http url
    transplatform_url = models.URLField(max_length=500)
    release_streams = ArrayField(
        models.CharField(max_length=400, blank=True),
        default=list, null=True
    )
    relstream_names = JSONField(null=True)
    lang_set = models.CharField(max_length=200)
    transtats_lastupdated = models.DateTimeField(null=True)
    package_details_json = JSONField(null=True)
    release_branch_mapping = JSONField(null=True)
    details_json_lastupdated = models.DateTimeField(null=True)

    class Meta:
        db_table = TABLE_PREFIX + 'packages'


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
        models.CharField(max_length=1000, blank=True),
        default=list, null=True
    )
    rule_langs = ArrayField(
        models.CharField(max_length=400, blank=True),
        default=list, null=True
    )
    rule_relbranch = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=True)
    rule_status = models.BooleanField()

    class Meta:
        db_table = TABLE_PREFIX + 'graphrules'
