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

# third party
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Submit, Layout, Field, HTML, Reset
)
from crispy_forms.bootstrap import (
    FormActions, InlineRadios, Div, InlineCheckboxes
)

# django
from django import forms


__all__ = ['NewPackageForm', 'NewReleaseBranchForm', 'NewGraphRuleForm']


class TextArrayField(forms.MultipleChoiceField):
    """
    Multiple Check Box Field
    """
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        if not isinstance(value, (list, tuple, set)):
            return [value]
        return value


class NewPackageForm(forms.Form):
    """
    Add new package to package list
    """
    transplatform_choices = ()
    relstream_choices = ()
    update_stats_choices = (('stats', 'Translation Stats'), )

    package_name = forms.CharField(
        label='Package Name', help_text='Package id as-in translation platform. Use hyphen (-) to separate words.', required=True,
    )
    upstream_url = forms.URLField(
        label='Upstream URL', help_text='Source repository location (Bitbucket, GitHub, Pagure etc).', required=True
    )
    transplatform_slug = forms.ChoiceField(
        label='Translation Platform',
        choices=transplatform_choices, help_text='Translation statistics will be fetched from this server.'
    )
    release_streams = TextArrayField(
        label='Release Stream', widget=forms.CheckboxSelectMultiple, choices=relstream_choices,
        help_text="Translation progress for selected streams will be tracked."
    )
    update_stats = forms.ChoiceField(
        label='Update details', widget=forms.CheckboxSelectMultiple, choices=update_stats_choices,
        help_text="Stats fetch would be attempted. <span class='text-warning'>This may take some time!</span>",
        required=False
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
    helper.form_action = '/settings/packages/new'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('package_name', css_class='form-control', onkeyup="showPackageSlug()"),
            Field('upstream_url', css_class='form-control', onkeyup="showUpstreamName()"),
            Field('transplatform_slug', css_class='selectpicker', onchange="showTransplatformId()"),
            InlineCheckboxes('release_streams'),
            InlineCheckboxes('update_stats'),
            HTML("<hr/>"),
            HTML("<h5 class='text-info'>Servers configured here may be contacted at intervals.</h5>"),
            FormActions(
                Submit('addPackage', 'Add Package'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True


class NewReleaseBranchForm(forms.Form):
    """
    Add new branch to release stream
    """
    action_url = ''
    phases_choices = ()
    langset_choices = ()
    enable_flags_choices = (('track_trans_flag', 'Track Translation'),
                            ('sync_calendar', 'Sync Calendar'),
                            ('notifications_flag', 'Notification'))

    relbranch_name = forms.CharField(
        label='Release Branch Name', help_text='Version of the release stream.', required=True,
    )
    current_phase = forms.ChoiceField(
        label='Current Phase', choices=phases_choices, required=True,
        help_text='Phase in which this version/branch is running.'
    )
    lang_set = forms.ChoiceField(
        label="Language Set", choices=langset_choices, required=True,
        help_text='Language set which should be associated with this branch.'
    )
    calendar_url = forms.URLField(
        label='iCal URL', help_text='Release schedule calendar URL. (Prefer translation specific)', required=True
    )
    enable_flags = TextArrayField(
        label='Enable flags', widget=forms.CheckboxSelectMultiple, choices=enable_flags_choices,
        help_text="Selected tasks will be enabled for this release version/branch.",
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.phases_choices = kwargs.pop('phases_choices')
        self.langset_choices = kwargs.pop('langset_choices')
        self.action_url = kwargs.pop('action_url')
        super(NewReleaseBranchForm, self).__init__(*args, **kwargs)
        self.fields['current_phase'].choices = self.phases_choices
        self.fields['lang_set'].choices = self.langset_choices
        super(NewReleaseBranchForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_action = action_url
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('relbranch_name', css_class='form-control', onkeyup="showBranchNameSlug()"),
            Field('current_phase', css_class='selectpicker'),
            Field('lang_set', css_class='selectpicker'),
            Field('calendar_url', css_class='form-control'),
            InlineCheckboxes('enable_flags'),
            HTML("<hr/>"),
            FormActions(
                Submit('addrelbranch', 'Add Release Branch'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True


class NewGraphRuleForm(forms.Form):
    """
    Add new graph rule
    """
    rule_packages_choices = ()
    rule_langs_choices = ()
    rule_relbranch_choices = (('master', 'master'), )

    rule_name = forms.CharField(
        label='Graph Rule Name', help_text='Rule will be saved in slug form.', required=True,
    )
    rule_packages = TextArrayField(
        label='Packages', widget=forms.CheckboxSelectMultiple, choices=rule_packages_choices,
        help_text="Selected packages will be included in this rule.", required=True
    )
    rule_langs = TextArrayField(
        label='Languages', widget=forms.CheckboxSelectMultiple, choices=rule_langs_choices,
        help_text="Selected languages will be included in this rule.", required=True
    )
    rule_relbranch = forms.ChoiceField(
        label='Release Branch', choices=rule_relbranch_choices,
        help_text='Graph will be generated for selected release branch.',
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.rule_packages_choices = kwargs.pop('packages')
        self.rule_langs_choices = kwargs.pop('languages')
        super(NewGraphRuleForm, self).__init__(*args, **kwargs)
        self.fields['rule_packages'].choices = self.rule_packages_choices
        self.fields['rule_langs'].choices = self.rule_langs_choices
        super(NewGraphRuleForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_action = '/settings/graph-rules/new'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('rule_name', css_class='form-control', onkeyup="showRuleSlug()"),
            InlineCheckboxes('rule_packages'),
            InlineCheckboxes('rule_langs'),
            Field('rule_relbranch', css_class='selectpicker'),
            HTML("<hr/>"),
            FormActions(
                Submit('addRule', 'Add Graph Rule'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True
