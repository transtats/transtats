# Copyright 2018 Red Hat, Inc.
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
import json
import yaml
from uuid import uuid4

# django
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

# third party
from rest_framework.authtoken.models import Token


TABLE_PREFIX = 'ts_'


class ModelMixin(object):

    @staticmethod
    def str2json(text_value):
        try:
            return json.loads(text_value)
        except Exception:
            return {}


class Language(models.Model):
    """
    Language Model
    """
    locale_id = models.CharField(
        max_length=50, primary_key=True, verbose_name="Locale ID"
    )
    lang_name = models.CharField(
        max_length=400, unique=True, verbose_name="Language Name"
    )
    locale_alias = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="Locale Alias"
    )
    locale_script = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Locale Script"
    )
    lang_status = models.BooleanField(verbose_name="Enable/Disable")

    def __str__(self):
        return self.lang_name

    class Meta:
        db_table = TABLE_PREFIX + 'languages'
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


class Platform(ModelMixin, models.Model):
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
    ci_status = models.BooleanField(verbose_name="CI Enable/Disable", default=False)
    projects_json_str = models.TextField(null=True, blank=True)
    projects_last_updated = models.DateTimeField(null=True)
    auth_login_id = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Auth User"
    )
    auth_token_key = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Auth Password/Token"
    )
    token_api_json_str = models.TextField(null=True, blank=True, verbose_name="Auth Token JSON")
    token_expiry = models.DateTimeField(null=True, blank=True, verbose_name="Auth Token Expiry")

    @property
    def projects_json(self):
        return self.str2json(self.projects_json_str)

    @property
    def token_api_json(self):
        return self.str2json(self.token_api_json_str)

    @property
    def token_status(self):
        if not self.token_expiry:
            return
        return self.token_expiry > timezone.now()

    def __str__(self):
        return "{0} {1}".format(self.engine_name, self.subject)

    class Meta:
        db_table = TABLE_PREFIX + 'platforms'
        verbose_name = "Translation Platform"


class Product(models.Model):
    """
    Product Model
    """
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(
        max_length=200, verbose_name="Product Name"
    )
    product_slug = models.CharField(
        max_length=400, unique=True, verbose_name="Product SLUG"
    )
    product_url = models.URLField(
        max_length=500, unique=True, verbose_name="Product URL", null=True
    )
    product_api_url = models.URLField(
        max_length=500, verbose_name="Product API URL", null=True
    )
    product_server = models.URLField(
        max_length=500, verbose_name="Product Server"
    )
    product_build_system = models.CharField(
        max_length=200, null=True, verbose_name="Release Build System"
    )
    product_build_tags = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=list, null=True, verbose_name="Release Build Tags"
    )
    product_build_tags_last_updated = models.DateTimeField(null=True)
    src_pkg_format = models.CharField(
        max_length=50, null=True, verbose_name="Source Package Format"
    )
    top_url = models.URLField(max_length=500, verbose_name="Top URL")
    web_url = models.URLField(max_length=500, null=True, verbose_name="Web URL")
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
    product_phases = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=list, null=True, verbose_name="Release Stream Phases"
    )
    product_status = models.BooleanField(verbose_name="Enable/Disable")

    def __str__(self):
        return self.product_name

    class Meta:
        db_table = TABLE_PREFIX + 'products'
        verbose_name = "Product"


class Release(ModelMixin, models.Model):
    """
    Releases Model
    """
    release_id = models.AutoField(primary_key=True)
    release_name = models.CharField(max_length=500, verbose_name="Release Name")
    release_slug = models.CharField(max_length=500, unique=True, verbose_name="Release SLUG")
    product_slug = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        to_field='product_slug', verbose_name="Product"
    )
    language_set_slug = models.ForeignKey(
        LanguageSet, on_delete=models.PROTECT,
        to_field='lang_set_slug', verbose_name="Language Set"
    )
    scm_branch = models.CharField(max_length=100, null=True, blank=True, verbose_name="SCM Branch Name")
    created_on = models.DateTimeField()
    current_phase = models.CharField(max_length=200, null=True, verbose_name="Current Phase")
    calendar_url = models.URLField(max_length=500, unique=True, null=True, verbose_name="Calender iCal URL")
    schedule_json_str = models.TextField(null=True, blank=True)
    sync_calendar = models.BooleanField(default=True, verbose_name="Sync Calender")
    notifications_flag = models.BooleanField(default=True, verbose_name="Notification")
    track_trans_flag = models.BooleanField(default=True, verbose_name="Track Translation")
    created_by = models.EmailField(null=True)

    @property
    def schedule_json(self):
        return self.str2json(self.schedule_json_str)

    def __str__(self):
        return self.release_name

    class Meta:
        db_table = TABLE_PREFIX + 'releases'
        verbose_name_plural = "Release"


class Package(ModelMixin, models.Model):
    """
    Packages Model
    """
    package_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=1000, unique=True, verbose_name="Package Name")
    upstream_name = models.CharField(max_length=1000, null=True, blank=True,
                                     verbose_name="Upstream Name")
    downstream_name = models.CharField(max_length=1000, null=True, blank=True,
                                       verbose_name="Downstream Name")
    component = models.CharField(max_length=200, null=True, blank=True, verbose_name="Component")
    upstream_url = models.URLField(max_length=2000, unique=True, verbose_name="Upstream URL")
    upstream_l10n_url = models.URLField(max_length=2000, null=True, blank=True,
                                        verbose_name="Upstream Localization URL")
    platform_slug = models.ForeignKey(
        Platform, on_delete=models.PROTECT,
        to_field='platform_slug', verbose_name="Translation Platform"
    )
    platform_name = models.CharField(max_length=1000, null=True, blank=True,
                                     verbose_name="Package Name at Translation Platform")
    # translation platform project http url
    platform_url = models.URLField(max_length=500, null=True, blank=True,
                                   verbose_name="Translation Platform Project URL")
    products = ArrayField(
        models.CharField(max_length=400, blank=True),
        default=list, null=True, verbose_name="Release Streams"
    )
    package_details_json_str = models.TextField(null=True, blank=True)
    details_json_last_updated = models.DateTimeField(null=True)
    package_name_mapping_json_str = models.TextField(null=True, blank=True)
    name_map_last_updated = models.DateTimeField(null=True, blank=True)
    release_branch_mapping = models.TextField(null=True, blank=True)
    release_branch_map_last_updated = models.DateTimeField(null=True, blank=True)
    package_latest_builds = models.TextField(null=True, blank=True)
    package_latest_builds_last_updated = models.DateTimeField(null=True, blank=True)
    stats_diff = models.TextField(null=True, blank=True)
    stats_diff_last_updated = models.DateTimeField(null=True, blank=True)
    platform_last_updated = models.DateTimeField(null=True, blank=True)
    upstream_last_updated = models.DateTimeField(null=True, blank=True)
    downstream_last_updated = models.DateTimeField(null=True, blank=True)
    translation_file_ext = models.CharField(
        max_length=10, null=True, blank=True, default='po',
        verbose_name="Translation Format (po)"
    )
    created_by = models.EmailField(null=True)
    maintainers = models.TextField(null=True, blank=True)

    @property
    def package_details_json(self):
        return self.str2json(self.package_details_json_str)

    @property
    def package_name_mapping_json(self):
        return self.str2json(self.package_name_mapping_json_str)

    @property
    def release_branch_mapping_json(self):
        return self.str2json(self.release_branch_mapping)

    @property
    def package_latest_builds_json(self):
        return self.str2json(self.package_latest_builds)

    @property
    def release_branch_mapping_health(self):
        release_branch_mapping_dict = \
            self.str2json(self.release_branch_mapping)
        if not release_branch_mapping_dict:
            return False
        for release, mapping in release_branch_mapping_dict.items():
            if isinstance(mapping, dict):
                for k, v in mapping.items():
                    if not mapping.get(k):
                        return False
        return True

    @property
    def stats_diff_json(self):
        return self.str2json(self.stats_diff)

    @property
    def stats_diff_health(self):
        stats_diff_dict = self.str2json(self.stats_diff)
        if not stats_diff_dict:
            return True
        for release, diff in stats_diff_dict.items():
            if stats_diff_dict.get(release):
                return False
        return True

    @property
    def maintainers_json(self):
        return self.str2json(self.maintainers)

    def __str__(self):
        return self.package_name

    class Meta:
        db_table = TABLE_PREFIX + 'packages'
        verbose_name = "Package"


class PackageSet(models.Model):
    """
    Package Set Model
    """
    package_set_id = models.AutoField(primary_key=True)
    package_set_name = models.CharField(
        max_length=1000, verbose_name="Package Set Name"
    )
    package_set_slug = models.CharField(
        max_length=400, unique=True, verbose_name="Package Set SLUG"
    )
    package_set_color = models.CharField(
        max_length=100, unique=True, verbose_name="Tag Colour"
    )
    packages = models.TextField(null=True, blank=True, verbose_name="Packages")

    def __str__(self):
        return self.package_set_name

    class Meta:
        db_table = TABLE_PREFIX + 'packageset'
        verbose_name = "Package Set"


class JobTemplate(ModelMixin, models.Model):
    """
    Job Templates Model
    """
    job_template_id = models.AutoField(primary_key=True)
    job_template_type = models.CharField(max_length=100, unique=True)
    job_template_name = models.CharField(max_length=500)
    job_template_desc = models.CharField(max_length=1000, blank=True, null=True)
    job_template_params = ArrayField(
        models.CharField(max_length=1000, blank=True), default=list
    )
    job_template_json_str = models.TextField(null=True, blank=True)
    job_template_last_accessed = models.DateTimeField(null=True)
    job_template_derived = models.BooleanField(default=False)

    @property
    def job_template_json(self):
        return self.str2json(self.job_template_json_str)

    def __str__(self):
        return self.job_template_name

    class Meta:
        db_table = TABLE_PREFIX + 'jobtemplates'
        verbose_name = "Job Template"


class CIPipeline(ModelMixin, models.Model):
    """
    Continuous Integration Pipeline Model
    """
    ci_pipeline_id = models.AutoField(primary_key=True)
    ci_pipeline_uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    ci_package = models.ForeignKey(
        Package, on_delete=models.PROTECT, verbose_name="Package"
    )
    ci_platform = models.ForeignKey(
        Platform, on_delete=models.PROTECT, verbose_name="Platform"
    )
    ci_release = models.ForeignKey(
        Release, on_delete=models.PROTECT, verbose_name="Release", null=True
    )
    ci_push_job_template = models.ForeignKey(
        JobTemplate, on_delete=models.PROTECT, verbose_name="Push Job Template",
        related_name="push_template", null=True
    )
    ci_pull_job_template = models.ForeignKey(
        JobTemplate, on_delete=models.PROTECT, verbose_name="Pull Job Template",
        related_name="pull_template", null=True
    )
    ci_project_web_url = models.URLField(max_length=500, null=True, blank=True,
                                         verbose_name="Platform Project URL")
    ci_project_details_json_str = models.TextField(null=True, blank=True)
    ci_platform_jobs_json_str = models.TextField(null=True, blank=True)
    ci_project_analyses_json_str = models.TextField(null=True, blank=True)
    ci_project_import_settings_json_str = models.TextField(null=True, blank=True)
    ci_project_assign_templates_json_str = models.TextField(null=True, blank=True)
    ci_project_workflow_steps_json_str = models.TextField(null=True, blank=True)
    ci_project_providers_json_str = models.TextField(null=True, blank=True)
    ci_project_term_bases_json_str = models.TextField(null=True, blank=True)
    ci_project_qa_checks_json_str = models.TextField(null=True, blank=True)
    ci_project_trans_memory_json_str = models.TextField(null=True, blank=True)
    ci_pipeline_last_updated = models.DateTimeField(null=True, blank=True)
    ci_pipeline_visibility = models.BooleanField(
        default=True, verbose_name='CI Pipeline Visibility'
    )
    ci_pipeline_default_branch = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Default Branch"
    )
    ci_pipeline_auto_create_config = models.BooleanField(
        default=True, verbose_name='Create default configurations', null=True, blank=True
    )

    @property
    def ci_project_details_json(self):
        return self.str2json(self.ci_project_details_json_str)

    @property
    def ci_platform_jobs_json(self):
        return self.str2json(self.ci_platform_jobs_json_str)

    @property
    def ci_project_analyses_json(self):
        return self.str2json(self.ci_project_analyses_json_str)

    @property
    def ci_project_import_settings_json(self):
        return self.str2json(self.ci_project_import_settings_json_str)

    @property
    def ci_project_assign_templates_json(self):
        return self.str2json(self.ci_project_assign_templates_json_str)

    @property
    def ci_project_workflow_steps_json(self):
        return self.str2json(self.ci_project_workflow_steps_json_str)

    @property
    def ci_project_providers_json(self):
        return self.str2json(self.ci_project_providers_json_str)

    @property
    def ci_project_term_bases_json(self):
        return self.str2json(self.ci_project_term_bases_json_str)

    @property
    def ci_project_qa_checks_json(self):
        return self.str2json(self.ci_project_qa_checks_json_str)

    @property
    def ci_project_trans_memory_json(self):
        return self.str2json(self.ci_project_trans_memory_json_str)

    def __str__(self):
        return "{} | {}".format(
            str(self.ci_pipeline_uuid)[:8],
            self.ci_package.package_name
        )

    class Meta:
        db_table = TABLE_PREFIX + 'cipipeline'
        verbose_name = "CI Pipeline"


class CIPlatformJob(ModelMixin, models.Model):
    """
    CI Pipeline Platform Job Model
    """
    ci_platform_job_id = models.AutoField(primary_key=True)
    ci_pipeline = models.ForeignKey(
        CIPipeline, on_delete=models.PROTECT,
        to_field="ci_pipeline_uuid", verbose_name="CI Pipeline"
    )
    ci_platform_job_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_analyses_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_segments_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_status_changes_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_trans_resources_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_workflow_step_json_str = models.TextField(null=True, blank=True)
    ci_platform_job_visibility = models.BooleanField(default=True)

    @property
    def ci_platform_job_json(self):
        return self.str2json(self.ci_platform_job_json_str)

    @property
    def ci_platform_job_analyses_json(self):
        return self.str2json(self.ci_platform_job_analyses_json_str)

    @property
    def ci_platform_job_segments_json(self):
        return self.str2json(self.ci_platform_job_segments_json_str)

    @property
    def ci_platform_job_status_changes_json(self):
        return self.str2json(self.ci_platform_job_status_changes_json_str)

    @property
    def ci_platform_job_trans_resources_json(self):
        return self.str2json(self.ci_platform_job_trans_resources_json_str)

    @property
    def ci_platform_job_workflow_step_json(self):
        return self.str2json(self.ci_platform_job_workflow_step_json_str)

    class Meta:
        db_table = TABLE_PREFIX + 'ciplatformjob'
        verbose_name = "CI Platform Job"


class PipelineConfig(ModelMixin, models.Model):
    """
    Pipeline Configurations Model
    """
    pipeline_config_id = models.AutoField(primary_key=True)
    ci_pipeline = models.ForeignKey(CIPipeline, on_delete=models.PROTECT,
                                    verbose_name="CI Pipeline", null=True)
    pipeline_config_event = models.CharField(max_length=1000)
    pipeline_config_active = models.BooleanField(default=False)
    pipeline_config_json_str = models.TextField()
    pipeline_config_repo_branches = ArrayField(
        models.CharField(max_length=1000, blank=True), default=list,
        verbose_name="Repo Branches"
    )
    pipeline_config_target_lang = ArrayField(
        models.CharField(max_length=1000, blank=True), default=list,
        verbose_name="Repo Target Langs"
    )
    pipeline_config_created_on = models.DateTimeField(null=True)
    pipeline_config_updated_on = models.DateTimeField(null=True)
    pipeline_config_last_accessed = models.DateTimeField(null=True)
    pipeline_config_created_by = models.EmailField(null=True)
    pipeline_config_is_default = models.BooleanField(default=False)

    @property
    def pipeline_config_json(self):
        return self.str2json(self.pipeline_config_json_str)

    @property
    def pipeline_config_yaml(self):
        return yaml.dump(
            self.str2json(self.pipeline_config_json_str),
            default_flow_style=False
        ).replace("\'", "")

    class Meta:
        db_table = TABLE_PREFIX + 'cipipelineconfig'
        constraints = [
            models.UniqueConstraint(fields=['pipeline_config_json_str', 'pipeline_config_repo_branches'],
                                    name='unique_pipeline_config')
        ]
        verbose_name = "Pipeline Config"


class Job(ModelMixin, models.Model):
    """
    Jobs Model
    """
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.UUIDField(default=uuid4, editable=False)
    job_type = models.CharField(max_length=200)
    job_start_time = models.DateTimeField()
    job_end_time = models.DateTimeField(null=True)
    job_yml_text = models.CharField(max_length=2000, null=True, blank=True)
    job_log_json_str = models.TextField(null=True, blank=True)
    job_result = models.NullBooleanField()
    job_remarks = models.CharField(max_length=200, null=True)
    job_template = models.ForeignKey(JobTemplate, on_delete=models.PROTECT,
                                     verbose_name="Job Template", null=True)
    ci_pipeline = models.ForeignKey(CIPipeline, on_delete=models.PROTECT,
                                    verbose_name="CI Pipeline", null=True)
    job_params_json_str = models.TextField(null=True, blank=True)
    job_output_json_str = models.TextField(null=True, blank=True)
    triggered_by = models.EmailField(null=True)
    job_visible_on_url = models.BooleanField(default=False)

    @property
    def job_log_json(self):
        return self.str2json(self.job_log_json_str)

    @property
    def job_params_json(self):
        return self.str2json(self.job_params_json_str)

    @property
    def job_output_json(self):
        return self.str2json(self.job_output_json_str)

    @property
    def duration(self):
        time_diff = self.job_end_time - self.job_start_time
        return time_diff.total_seconds()

    class Meta:
        db_table = TABLE_PREFIX + 'jobs'
        verbose_name = "Job"


class SyncStats(ModelMixin, models.Model):
    """
    Sync Stats Model
    """
    sync_id = models.AutoField(primary_key=True)
    package_name = models.ForeignKey(
        Package, on_delete=models.PROTECT,
        to_field='package_name', verbose_name="Package"
    )
    job_uuid = models.UUIDField()
    project_version = models.CharField(max_length=500, null=True)
    source = models.CharField(max_length=500, null=True)
    stats_raw_json_str = models.TextField(null=True, blank=True)
    stats_processed_json_str = models.TextField(null=True, blank=True)
    sync_iter_count = models.IntegerField()
    sync_visibility = models.BooleanField()

    @property
    def stats_raw_json(self):
        return self.str2json(self.stats_raw_json_str)

    @property
    def stats_processed_json(self):
        return self.str2json(self.stats_processed_json_str)

    class Meta:
        db_table = TABLE_PREFIX + 'syncstats'


class GraphRule(models.Model):
    """
    Graph Rules Model
    """
    graph_rule_id = models.AutoField(primary_key=True)
    rule_name = models.CharField(max_length=1000, unique=True,
                                 verbose_name="Rule Name")
    rule_packages = ArrayField(
        models.CharField(max_length=1000, blank=True), default=list,
        verbose_name="Rule Packages"
    )
    rule_languages = ArrayField(
        models.CharField(max_length=400, blank=True), default=list,
        verbose_name="Rule Languages"
    )
    rule_release_slug = models.ForeignKey(
        Release, on_delete=models.PROTECT,
        to_field='release_slug', verbose_name="Release"
    )
    rule_build_tags = ArrayField(
        models.CharField(max_length=200, blank=True),
        default=list, null=True, verbose_name="Rule Build Tags"
    )
    created_on = models.DateTimeField()
    rule_status = models.BooleanField(default=True)
    rule_visibility_public = models.BooleanField(default=False)
    created_by = models.EmailField(null=True)

    def __str__(self):
        return self.rule_name

    class Meta:
        db_table = TABLE_PREFIX + 'graphrules'
        verbose_name = "Graph Rule"


class CacheAPI(ModelMixin, models.Model):
    """
    Cache API Model
    """
    cache_api_id = models.AutoField(primary_key=True)
    base_url = models.URLField(max_length=800)
    resource = models.CharField(max_length=200)
    request_args = ArrayField(
        models.CharField(max_length=400, blank=True), default=list
    )
    request_kwargs = models.CharField(max_length=1000)
    response_content = models.TextField(max_length=10000)
    response_content_json_str = models.TextField(null=True, blank=True)
    expiry = models.DateTimeField()

    @property
    def response_content_json(self):
        return self.str2json(self.response_content_json_str)

    class Meta:
        db_table = TABLE_PREFIX + 'cacheapi'


class CacheBuildDetails(ModelMixin, models.Model):
    """
    Cache Build Details Model
    """
    cache_build_details_id = models.AutoField(primary_key=True)
    package_name = models.ForeignKey(
        Package, on_delete=models.PROTECT,
        to_field='package_name', verbose_name="Package"
    )
    build_system = models.CharField(
        max_length=200, verbose_name="Build System"
    )
    build_tag = models.CharField(
        max_length=200, verbose_name="Build Tag"
    )
    build_details_json_str = models.TextField(null=True, blank=True)
    job_log_json_str = models.TextField(null=True, blank=True)

    @property
    def build_details_json(self):
        return self.str2json(self.build_details_json_str)

    @property
    def job_log_json(self):
        return self.str2json(self.job_log_json_str)

    class Meta:
        db_table = TABLE_PREFIX + 'cachebuilddetails'


class Report(ModelMixin, models.Model):
    """
    Reports Model
    """
    reports_id = models.AutoField(primary_key=True)
    report_subject = models.CharField(max_length=200, unique=True)
    report_json_str = models.TextField(null=True, blank=True)
    report_updated = models.DateTimeField(null=True)

    @property
    def report_json(self):
        return self.str2json(self.report_json_str)

    def __str__(self):
        return self.report_subject

    class Meta:
        db_table = TABLE_PREFIX + 'reports'
        verbose_name = "Report"


class Visitor(models.Model):
    """
    Visitors Model
    """
    visitor_id = models.AutoField(primary_key=True)
    visitor_ip = models.GenericIPAddressField()
    visitor_user_agent = models.CharField(max_length=500)
    visitor_accept = models.CharField(max_length=500, null=True, blank=True)
    visitor_encoding = models.CharField(max_length=500, null=True, blank=True)
    visitor_language = models.CharField(max_length=500, null=True, blank=True)
    visitor_host = models.CharField(max_length=500, null=True, blank=True)
    first_visit_time = models.DateTimeField()
    last_visit_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.visitor_id:
            self.first_visit_time = timezone.now()
        self.last_visit_time = timezone.now()
        return super(Visitor, self).save(*args, **kwargs)

    def __str__(self):
        return "%s: %s" % (str(self.visitor_ip), self.visitor_user_agent)

    class Meta:
        db_table = TABLE_PREFIX + 'visitors'
        verbose_name = "Visitor"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
