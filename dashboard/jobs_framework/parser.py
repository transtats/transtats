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

from yaml import load, YAMLError, FullLoader

__all__ = ['YMLPreProcessor', 'YMLJobParser']


class YMLPreProcessor(object):
    """Load and form YML, fill values"""

    delimiter = '%'

    def __init__(self, YML_Source, **vars):
        for attrib, value in vars.items():
            setattr(self, str(attrib), value)
        self.YML = YML_Source
        self.variables = [segment for segment in self.YML.split()
                          if segment.startswith(self.delimiter) and
                          segment.endswith(self.delimiter)]

    @property
    def output(self):
        in_process_text = self.YML
        for variable in self.variables:
            in_process_text = in_process_text.replace(
                variable, getattr(self, variable.replace(self.delimiter, ''), '')
            )
        return in_process_text


class YMLJobParser(object):
    """Parse YML and build objects"""
    test_yml_path = 'dashboard/tests/testdata/job-templates/stringchange.yml'

    def __init__(self, yml_stream=None):

        stream = yml_stream if yml_stream else open(self.test_yml_path)
        try:
            parsed_data = load(stream, Loader=FullLoader)
        except YAMLError as exc:
            # log error
            pass
        else:
            if isinstance(parsed_data, dict):
                self.data = parsed_data.get('job', {})

    @property
    def buildsys(self):
        return self.data.get('buildsys', '')

    @property
    def release(self):
        return self.data.get('release', '')

    @property
    def ci_pipeline(self):
        return self.data.get('ci_pipeline', '')

    @property
    def exception(self):
        return self.data.get('exception', '')

    @property
    def execution(self):
        return self.data.get('execution', '')

    @property
    def job_name(self):
        return self.data.get('name', '')

    @property
    def job_type(self):
        return self.data.get('type', '')

    @property
    def package(self):
        return self.data.get('package', '')

    @property
    def return_type(self):
        return self.data.get('return_type', '')

    @property
    def tags(self):
        return self.data.get('tags', [])

    @property
    def tasks(self):
        return self.data.get('tasks', [])
