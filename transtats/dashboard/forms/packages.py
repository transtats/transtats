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
    FormActions, InlineRadios, Div, InlineCheckboxes
)


class NewPackageForm(forms.Form):
    """
    Add new package to package list
    """
    transplatform_choices = ()
    relstream_choices = ()
    langset_choices = (('default', 'Default'), ('custom', 'Custom'))

    package_name = forms.CharField(
        label='Package Name', help_text='Package name as-in translation platform.', required=True,
    )
    upstream_url = forms.URLField(
        label='Upstream URL', help_text='Source repository location (GitHub, Bitbucket etc).', required=True
    )
    transplatform_slug = forms.ChoiceField(
        label='Translation Platform',
        choices=transplatform_choices, help_text='Translation statistics will be fetched from this server.'
    )
    release_streams = forms.ChoiceField(
        label='Release Stream', widget=forms.CheckboxSelectMultiple, choices=relstream_choices,
        help_text="Translation progress for selected streams will be tracked."
    )
    lang_set = forms.ChoiceField(
        label="Language Set", widget=forms.RadioSelect, choices=langset_choices, required=False
    )

    def __init__(self, *args, **kwargs):
        self.transplatform_choices = kwargs.pop('transplatform_choices')
        self.relstream_choices = kwargs.pop('relstream_choices')
        super(NewPackageForm, self).__init__(*args, **kwargs)
        self.fields['transplatform_slug'].choices = self.transplatform_choices
        self.fields['release_streams'].choices = self.relstream_choices
        super(NewPackageForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_action = '/settings/packages'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('package_name', css_class='form-control'),
            Field('upstream_url', css_class='form-control'),
            Field('transplatform_slug', css_class='selectpicker'),
            InlineCheckboxes('release_streams'),
            InlineRadios('lang_set'),
            HTML("<hr/>"),
            HTML("<h5 class='text-info'>Servers configured here may be contacted at intervals.</h5>"),
            FormActions(
                Submit('addPackage', 'Add Package'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True
