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

# dashboard
from dashboard.models import (Languages, LanguageSet, TransPlatform, Packages)
from dashboard.managers.inventory import InventoryManager
from dashboard.managers.packages import PackagesManager
from dashboard.constants import (
    TRANSPLATFORM_ENGINES,
    TRANSIFEX_SLUGS, ZANATA_SLUGS, DAMNEDLIES_SLUGS
)

__all__ = ['NewPackageForm', 'NewReleaseBranchForm', 'NewGraphRuleForm']

ENGINE_CHOICES = tuple([(engine, engine.upper())
                        for engine in TRANSPLATFORM_ENGINES])

all_platform_slugs = []
all_platform_slugs.extend(TRANSIFEX_SLUGS)
all_platform_slugs.extend(ZANATA_SLUGS)
all_platform_slugs.extend(DAMNEDLIES_SLUGS)
SLUG_CHOICES = tuple([(slug, slug) for slug in all_platform_slugs])


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
    helper.form_action = '/packages/new'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('package_name', css_class='form-control', onkeyup="showPackageSlug()"),
            Field('upstream_url', css_class='form-control'),
            Field('transplatform_slug', css_class='selectpicker'),
            InlineCheckboxes('release_streams'),
            InlineCheckboxes('update_stats'),
            HTML("<hr/>"),
            HTML("<h5 class='text-info'>Servers configured here may be contacted at intervals.</h5>"),
            FormActions(
                Submit('addPackage', 'Add Package'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True


class UpdatePackageForm(forms.ModelForm):
    """
    Update package form
    """
    release_streams = TextArrayField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(UpdatePackageForm, self).__init__(*args, **kwargs)
        inventory_manager = InventoryManager()
        self.fields['transplatform_slug'].choices = inventory_manager.get_transplatform_slug_url()
        self.fields['release_streams'].choices = inventory_manager.get_relstream_slug_name()

    class Meta:
        model = Packages
        fields = ['package_name', 'upstream_url', 'transplatform_slug', 'release_streams', 'release_branch_mapping']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('package_name', css_class='form-control', readonly=True),
            Field('upstream_url', css_class='form-control'),
            Field('transplatform_slug', css_class='selectpicker'),
            InlineCheckboxes('release_streams'),
            Field('release_branch_mapping', css_class='form-control', rows=4),
            FormActions(
                Submit('updatePackage', 'Update Package'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_package_name(self):
        """
        Don't allow to override the value of 'package_name' as it is readonly field
        """
        package_name = getattr(self.instance, 'package_name', None)
        if package_name:
            return package_name
        else:
            return self.cleaned_data.get('package_name', None)

    def clean(self):
        """
        Check if the package name exist on the selected translation platform, if not add error message for package_name
        """
        cleaned_data = super().clean()
        package_name = cleaned_data['package_name']
        transplatform_slug = getattr(cleaned_data['transplatform_slug'], 'platform_slug', None)
        packages_manager = PackagesManager()
        validate_package = packages_manager.validate_package(package_name=package_name,
                                                             transplatform_slug=transplatform_slug)
        if not validate_package:
            self.add_error('package_name', "Not found at selected translation platform")


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
    # Placeholder field for showing the slug on the form, this will be disabled
    relbranch_slug = forms.CharField(label='Release Branch Slug')
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
            Field('relbranch_slug', disabled=True),
            Field('current_phase', css_class='selectpicker'),
            Field('lang_set', css_class='selectpicker'),
            Field('calendar_url', css_class='form-control'),
            InlineCheckboxes('enable_flags'),
            HTML("<hr/>"),
            FormActions(
                Submit('addrelbranch', 'Add Release Branch'), Reset('reset', 'Reset', css_class='btn-danger')
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
    rule_relbranch_choices = ()

    rule_name = forms.CharField(
        label='Graph Rule Name', help_text='Rule will be saved in slug form.', required=True,
    )
    rule_relbranch = forms.ChoiceField(
        label='Release Branch', choices=rule_relbranch_choices,
        help_text='Graph will be generated for selected release branch following branch mapping.',
        required=True
    )
    rule_packages = TextArrayField(
        label='Packages', widget=forms.CheckboxSelectMultiple, choices=rule_packages_choices,
        help_text="Selected packages will be included in this rule.", required=True
    )
    lang_selection = forms.ChoiceField(
        label='Languages Selection', choices=[
            ('pick', 'Pick release branch specific languages'),
            ('select', 'Select languages')],
        initial='pick', widget=forms.RadioSelect, required=True,
        help_text="Either pick language set associated with selected release branch or choose languages."
    )
    rule_langs = TextArrayField(
        label='Languages', widget=forms.CheckboxSelectMultiple, choices=rule_langs_choices,
        help_text="Selected languages will be included in this rule.", required=False
    )

    def __init__(self, *args, **kwargs):
        self.rule_packages_choices = kwargs.pop('packages')
        self.rule_langs_choices = kwargs.pop('languages')
        self.rule_relbranch_choices = kwargs.pop('branches')
        super(NewGraphRuleForm, self).__init__(*args, **kwargs)
        self.fields['rule_packages'].choices = self.rule_packages_choices
        self.fields['rule_langs'].choices = self.rule_langs_choices
        self.fields['rule_relbranch'].choices = self.rule_relbranch_choices
        super(NewGraphRuleForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_action = '/settings/graph-rules/new'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('rule_name', css_class="form-control", onkeyup="showRuleSlug()"),
            Field('rule_relbranch', css_class="selectpicker"),
            InlineCheckboxes('rule_packages', css_class="checkbox"),
            InlineRadios('lang_selection', id="lang_selection_id"),
            InlineCheckboxes('rule_langs', css_class="checkbox"),
            HTML("<hr/>"),
            FormActions(
                Submit('addRule', 'Add Graph Rule'), Reset('reset', 'Reset')
            )
        )
    )

    def is_valid(self):
        return False if len(self.errors) >= 1 else True


class NewLanguageForm(forms.ModelForm):
    """
    Add new language form
    """
    def __init__(self, *args, **kwargs):
        super(NewLanguageForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Languages
        fields = '__all__'

    locale_id = forms.SlugField(label='Locale ID')
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('lang_name', css_class='form-control'),
            Field('locale_id', css_class='form-control'),
            Field('locale_alias', css_class='form-control'),
            Field('lang_status', css_class='bootstrap-switch'),
            FormActions(
                Submit('addLanguage', 'Add Language'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )


class UpdateLanguageForm(forms.ModelForm):
    """
    Update language form
    """
    def __init__(self, *args, **kwargs):
        super(UpdateLanguageForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Languages
        fields = '__all__'

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('locale_id', css_class='form-control', readonly=True),
            Field('lang_name', css_class='form-control'),
            Field('locale_alias', css_class='form-control'),
            Field('lang_status', css_class='bootstrap-switch'),
            FormActions(
                Submit('updateLanguage', 'Update Language'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_locale_id(self):
        """
        Set the original value of locale_id even if POST has new value. Retrieves value from instance of Languages
        being updated. If it's None, then returns the value entered by user.
        """
        locale_id = getattr(self.instance, 'locale_id', None)
        if locale_id:
            return locale_id
        else:
            return self.cleaned_data.get('locale_id', None)


class LanguageSetForm(forms.ModelForm):
    """
    Language set form, for new language set and update language set
    """
    class Meta:
        model = LanguageSet
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(LanguageSetForm, self).__init__(*args, **kwargs)
        inventory_manager = InventoryManager()
        self.fields['locale_ids'].choices = tuple([(locale.locale_id, locale.lang_name)
                                                   for locale in inventory_manager.get_locales()])

    lang_set_slug = forms.SlugField(label='Language Set SLUG')
    locale_ids = TextArrayField(label='Locale IDs', widget=forms.SelectMultiple,)
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('lang_set_name', css_class='form-control'),
            Field('lang_set_slug', css_class='form-control'),
            Field('lang_set_color', css_class='form-control'),
            Field('locale_ids', css_class='selectpicker'),
            FormActions(
                Submit('addLanguageSet', 'Add Language Set'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )


class NewTransPlatformForm(forms.ModelForm):
    """
    Add new TransPlatform form
    """
    def __init__(self, *args, **kwargs):
        super(NewTransPlatformForm, self).__init__(*args, **kwargs)

    class Meta:
        model = TransPlatform
        fields = ['engine_name', 'subject', 'api_url', 'platform_slug', 'server_status', 'server_status',
                  'auth_login_id', 'auth_token_key']

    engine_name = forms.ChoiceField(
        choices=ENGINE_CHOICES, label="Platform Engine",
        help_text="Platform engine helps system to determine specific API/tasks."
    )
    platform_slug = forms.ChoiceField(
        choices=SLUG_CHOICES, label="Platform SLUG",
        help_text="Please identify SLUG carefully. Example: ZNTAPUB should be for zanata public instance.",
    )
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('engine_name', css_class='form-control'),
            Field('subject', css_class='form-control'),
            Field('api_url', css_class='form-control'),
            Field('platform_slug', css_class='form-control'),
            Field('server_status', css_class='bootstrap-switch'),
            Field('auth_login_id', css_class='form-control'),
            Field('auth_token_key', css_class='form-control'),
            FormActions(
                Submit('addTransPlatform', 'Add Translation Platform'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )


class UpdateTransPlatformForm(forms.ModelForm):
    """
    Update TransPlatform form
    """
    def __init__(self, *args, **kwargs):
        super(UpdateTransPlatformForm, self).__init__(*args, **kwargs)

    class Meta:
        model = TransPlatform
        fields = ['engine_name', 'subject', 'api_url', 'platform_slug', 'server_status',
                  'auth_login_id', 'auth_token_key']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('engine_name', css_class='form-control', readonly=True),
            Field('subject', css_class='form-control'),
            Field('api_url', css_class='form-control'),
            Field('platform_slug', css_class='form-control', readonly=True),
            Field('server_status', css_class='bootstrap-switch'),
            Field('auth_login_id', css_class='form-control'),
            Field('auth_token_key', css_class='form-control'),
            FormActions(
                Submit('updateTransPlatform', 'Update Translation Platform'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_engine_name(self):
        """
        Don't allow to override the value of 'engine_name' as it is readonly field
        """
        engine_name = getattr(self.instance, 'engine_name', None)
        if engine_name:
            return engine_name
        else:
            return self.cleaned_data.get('engine_name', None)

    def clean_platform_slug(self):
        """
        Don't allow to override the value of 'platform_slug' as it is readonly field
        """
        platform_slug = getattr(self.instance, 'platform_slug', None)
        if platform_slug:
            return platform_slug
        else:
            return self.cleaned_data.get('platform_slug', None)
