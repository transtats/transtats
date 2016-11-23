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

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Submit, Layout, Field, HTML, Reset
)
from crispy_forms.bootstrap import (
    FormActions, Div, InlineCheckboxes
)


class NewReleaseBranchForm(forms.Form):
    """
    Add new branch to release stream
    """
    action_url = ''
    phases_choices = ()
    enable_flags_choices = (('track_trans_flag', 'Track Translation'),
                            ('sync_calender', 'Sync Calendar'),
                            ('notifications_flag', 'Notification'))

    relbranch_name = forms.CharField(
        label='Release Branch Name', help_text='Version of the release stream.', required=True,
    )
    current_phase = forms.ChoiceField(
        label='Current Phase', choices=phases_choices,
        help_text='Phase in which this version/branch is running.'
    )
    calender_url = forms.URLField(
        label='iCal URL', help_text='Release schedule calendar URL.', required=True
    )
    enable_flags = forms.ChoiceField(
        label='Enable flags', widget=forms.CheckboxSelectMultiple, choices=enable_flags_choices,
        help_text="Selected tasks would be enabled for this release version/branch.",
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.phases_choices = kwargs.pop('phases_choices')
        self.action_url = kwargs.pop('action_url')
        super(NewReleaseBranchForm, self).__init__(*args, **kwargs)
        self.fields['current_phase'].choices = self.phases_choices
        super(NewReleaseBranchForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_action = action_url
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('relbranch_name', css_class='form-control'),
            Field('current_phase', css_class='selectpicker'),
            Field('calender_url', css_class='form-control'),
            InlineCheckboxes('enable_flags'),
            HTML("<hr/>"),
            FormActions(
                Submit('addrelbranch', 'Add Release Branch'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True
