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

# Common functions/utilities

# python
from collections import OrderedDict

# dashboard
from dashboard.constants import (TRANSPLATFORM_ENGINES, RELSTREAM_SLUGS)


__all__ = ['parse_project_details_json', 'parse_ical_file']


def parse_project_details_json(engine, json_dict):
    """
    Parse project details json
    """
    if not isinstance(json_dict, dict):
        json_dict = {}
    project = ''
    versions = []
    if engine == TRANSPLATFORM_ENGINES[0]:
        project = json_dict.get('fields', {}).get('name')
        versions = json_dict.get('releases', [])
    elif engine == TRANSPLATFORM_ENGINES[1]:
        project = json_dict.get('slug', '')
        versions = [version.get('slug') for version in json_dict.get('resources', [])]
    elif engine == TRANSPLATFORM_ENGINES[2]:
        project = json_dict.get('id', '')
        versions = [version.get('id') for version in json_dict.get('iterations', [])
                    if version.get('status', '') == 'ACTIVE']
    elif engine == TRANSPLATFORM_ENGINES[3]:
        project = json_dict.get('slug', '')
        versions = [version.get('slug') for version in json_dict.get('components', [])]
    return project, versions


def parse_ical_file(ical_content, relstream_slug):
    """
    Parse iCal Content
    :param ical_content: Calendar Content
    :param ical_content: Release Stream Slug
    :return: dict_list
    """
    ical_calendar = []
    if not isinstance(ical_content, (list, tuple, set)):
        return ical_calendar

    DELIMITER = ":"
    EVENT_BEGIN_SYMBOL = ""
    EVENT_END_SYMBOL = ""

    if relstream_slug in (RELSTREAM_SLUGS[0], RELSTREAM_SLUGS[2]):
        EVENT_BEGIN_SYMBOL = "BEGIN:VEVENT"
        EVENT_END_SYMBOL = "END:VEVENT"
    elif relstream_slug == RELSTREAM_SLUGS[1]:
        EVENT_BEGIN_SYMBOL = "BEGIN:VTODO"
        EVENT_END_SYMBOL = "END:VTODO"

    append_flag = False
    ical_events = OrderedDict()
    for elem in ical_content:
        if elem == EVENT_END_SYMBOL:
            append_flag = False
            ical_calendar.append(ical_events)
            ical_events = OrderedDict()
        if append_flag:
            if ":" in elem:
                key_value = elem.split(DELIMITER)
                ical_events.update({key_value[0]: DELIMITER.join(key_value[1:])}) \
                    if key_value[0] == 'SUMMARY' \
                    else ical_events.update({key_value[0]: key_value[1]})
        if elem == EVENT_BEGIN_SYMBOL:
            append_flag = True
    return ical_calendar
