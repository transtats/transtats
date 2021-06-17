# Copyright 2020 Red Hat, Inc.
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

from mock import patch
from fixture import DjangoFixture
from fixture.style import NamedDataStyle
from fixture.django_testcase import FixtureTestCase

from dashboard.constants import TS_JOB_TYPES
from dashboard.managers.jobs import JobTemplateManager
from dashboard.managers.pipelines import CIPipelineManager
from dashboard.tests.testdata.db_fixtures import (
    JobTemplateData, CIPipelineData
)

db_fixture = DjangoFixture(style=NamedDataStyle())


class JobTemplateManagerTest(FixtureTestCase):

    job_template_manager = JobTemplateManager()
    fixture = db_fixture
    datasets = [JobTemplateData]

    def test_get_job_templates(self):
        """
        Test get_job_templates
        """
        templates = self.job_template_manager.get_job_templates()
        self.assertEqual(len(templates), 2, "two job templates")
        templates = self.job_template_manager.get_job_templates(
            'job_template_name', **{'job_template_type': TS_JOB_TYPES[2]}
        )
        self.assertEqual(len(templates), 1, "one filtered job template")
        self.assertEqual(templates[0].job_template_name, 'Clone Upstream Repo')


class CIPipelineManagerTest(FixtureTestCase):

    ci_pipeline_manager = CIPipelineManager()
    fixture = db_fixture
    datasets = [CIPipelineData]

    def xtest_get_ci_pipelines(self):
        """
        Test get_ci_pipelines
        """
        ci_pipelines = self.ci_pipeline_manager.get_ci_pipelines()
        self.assertEqual(len(ci_pipelines), 1, "one ci pipeline")
        self.assertEquals(ci_pipelines[0].ci_package.package_name, 'anaconda')
        self.assertEquals(ci_pipelines[0].ci_platform.platform_slug, 'MSRCPUB')
        self.assertEquals(ci_pipelines[0].ci_release.release_name, 'Fedora 27')
