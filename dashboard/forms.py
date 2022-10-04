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
    Submit, Layout, Field, HTML, Reset, Row
)
from crispy_forms.bootstrap import (
    FormActions, InlineRadios, Div, InlineCheckboxes, PrependedText
)
from slugify import slugify
from urllib.parse import urlparse

# django
from django import forms

# dashboard
from dashboard.models import (
    Language, LanguageSet, Platform, Package, GraphRule, CIPipeline
)
from dashboard.managers.inventory import InventoryManager
from dashboard.managers.packages import PackagesManager
from dashboard.constants import (
    TRANSPLATFORM_ENGINES,
    TRANSIFEX_SLUGS, ZANATA_SLUGS, DAMNEDLIES_SLUGS, WEBLATE_SLUGS, MEMSOURCE_SLUGS
)

__all__ = ['NewPackageForm', 'UpdatePackageForm', 'NewReleaseBranchForm',
           'NewGraphRuleForm', 'NewLanguageForm', 'UpdateLanguageForm',
           'LanguageSetForm', 'NewTransPlatformForm', 'UpdateTransPlatformForm',
           'UpdateGraphRuleForm', 'PackagePipelineForm', 'CreateCIPipelineForm']

ENGINE_CHOICES = tuple([(engine, engine.upper())
                        for engine in TRANSPLATFORM_ENGINES])

all_platform_slugs = []
all_platform_slugs.extend(TRANSIFEX_SLUGS)
all_platform_slugs.extend(ZANATA_SLUGS)
all_platform_slugs.extend(DAMNEDLIES_SLUGS)
all_platform_slugs.extend(WEBLATE_SLUGS)
all_platform_slugs.extend(MEMSOURCE_SLUGS)
SLUG_CHOICES = tuple([(slug, slug) for slug in all_platform_slugs])


class TextArrayField(forms.MultipleChoiceField):
    """Multiple Check Box Field"""
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        if not isinstance(value, (list, tuple, set)):
            return [value]
        return value


class NewPackageForm(forms.Form):
    """Add new package to package list"""
    platform_choices = ()
    products_choices = ()

    package_name = forms.CharField(
        label='Package Name', help_text='Package id as-in translation platform. Use hyphen (-) to separate words.', required=True,
    )
    upstream_url = forms.URLField(
        label='Upstream URL', help_text='Source repository location (Bitbucket, GitHub, Pagure etc).', required=True
    )
    upstream_l10n_url = forms.URLField(
        label='Upstream Localization URL', help_text='Optional. Source repository location with translation resources.', required=False
    )
    transplatform_slug = forms.ChoiceField(
        label='Translation Platform',
        choices=platform_choices, help_text='Translation statistics will be fetched from this server.'
    )
    auto_create_project = TextArrayField(
        label="Create Project at Platform",
        widget=forms.CheckboxSelectMultiple, choices=(('True', 'Yes'),),
        help_text="Attempt project creation at platform if it does not exist.", required=False
    )
    release_streams = TextArrayField(
        label='Products', widget=forms.CheckboxSelectMultiple, choices=products_choices,
        help_text="Translation progress for selected products will be tracked."
    )

    def __init__(self, *args, **kwargs):
        self.platform_choices = kwargs.pop('platform_choices')
        self.products_choices = kwargs.pop('products_choices')
        super(NewPackageForm, self).__init__(*args, **kwargs)
        self.fields['transplatform_slug'].choices = self.platform_choices
        self.fields['release_streams'].choices = self.products_choices
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
            Field('upstream_l10n_url', css_class='form-control'),
            Field('transplatform_slug', css_class='selectpicker'),
            InlineCheckboxes('auto_create_project'),
            InlineCheckboxes('release_streams'),
            HTML("<hr/>"),
            HTML("<h5 class='text-info'>Servers configured here may be contacted at intervals.</h5>"),
            FormActions(
                Submit('addPackage', 'Add Package'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def is_valid(self):
        return not len(self.errors) >= 1


class UpdatePackageForm(forms.ModelForm):
    """Update package form"""
    products = TextArrayField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(UpdatePackageForm, self).__init__(*args, **kwargs)
        inventory_manager = InventoryManager()
        self.fields['platform_slug'].choices = inventory_manager.get_transplatform_slug_url()
        self.fields['products'].choices = inventory_manager.get_relstream_slug_name()

    class Meta:
        model = Package
        fields = ['package_name', 'upstream_url', 'upstream_l10n_url', 'downstream_name',
                  'platform_slug', 'platform_url', 'products', 'release_branch_mapping']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('package_name', css_class='form-control', readonly=True),
            Field('upstream_url', css_class='form-control'),
            Field('upstream_l10n_url', css_class='form-control'),
            Field('downstream_name', css_class='form-control'),
            Field('platform_slug', css_class='selectpicker'),
            Field('platform_url', css_class='form-control', readonly=True),
            InlineCheckboxes('products'),
            Field('release_branch_mapping', css_class='form-control', rows=4, readonly=True),
            FormActions(
                Submit('updatePackage', 'Update Package'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_package_name(self):
        """Don't allow to override the value of 'package_name' as it is readonly field"""
        package_name = getattr(self.instance, 'package_name', None)
        if package_name:
            return package_name
        else:
            return self.cleaned_data.get('package_name', None)

    def clean(self):
        """
        Check if the package name exist on the selected translation platform,
        if not add error message for package_name
        """
        cleaned_data = super().clean()
        package_name = cleaned_data['package_name']
        platform_slug = getattr(cleaned_data['platform_slug'], 'platform_slug', None)
        platform_url = cleaned_data['platform_url']
        packages_manager = PackagesManager()
        pkg_platform_url, _ = packages_manager.get_project_details(cleaned_data['platform_slug'],
                                                                   package_name)
        if not platform_url == pkg_platform_url:
            cleaned_data['platform_url'] = pkg_platform_url
        validate_package = packages_manager.validate_package(package_name=package_name,
                                                             transplatform_slug=platform_slug)
        if not validate_package:
            self.add_error('package_name', "Not found at selected translation platform")
        else:
            old_platform_engine = getattr(getattr(getattr(self, 'instance', None), 'platform_slug', None),
                                          'engine_name', None)
            if old_platform_engine:
                packages_manager.syncstats_manager.toggle_visibility(
                    package=package_name, stats_source=old_platform_engine
                )
            new_platform_engine = packages_manager.get_engine_from_slug(platform_slug)
            if new_platform_engine:
                packages_manager.syncstats_manager.toggle_visibility(
                    package=package_name, stats_source=new_platform_engine
                )


class NewReleaseBranchForm(forms.Form):
    """Add new branch to release stream"""
    action_url = ''
    phases_choices = ()
    langset_choices = ()
    enable_flags_choices = (('track_trans_flag', 'Track Translation'),
                            ('sync_calendar', 'Sync Calendar'),
                            ('notifications_flag', 'Notification'))

    release_name = forms.CharField(
        label='Release Branch Name', help_text='Product release name with version.', required=True,
    )
    # Placeholder field for showing the slug on the form, this will be disabled
    relbranch_slug = forms.CharField(
        label='Release Slug', help_text='Slug will be validated with the iCal.'
    )
    current_phase = forms.ChoiceField(
        label='Current Phase', choices=phases_choices, required=True,
        help_text='Phase in which this release is running.'
    )
    lang_set = forms.ChoiceField(
        label="Language Set", choices=langset_choices, required=True,
        help_text='Language set which should be associated with this release.'
    )
    calendar_url = forms.URLField(
        label='iCal URL', help_text='Release schedule calendar URL. (Prefer translation specific)', required=True
    )
    scm_branch = forms.CharField(
        label='SCM Branch', required=False,
        help_text='Release Build System Default Tag.'
    )
    enable_flags = TextArrayField(
        label='Enable flags', widget=forms.CheckboxSelectMultiple, choices=enable_flags_choices,
        help_text="Selected tasks will be enabled for this release.",
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
            Field('release_name', css_class='form-control', onkeyup="showBranchNameSlug()"),
            Field('relbranch_slug', disabled=True),
            Field('current_phase', css_class='selectpicker'),
            Field('lang_set', css_class='selectpicker'),
            Field('calendar_url', css_class='form-control'),
            Field('scm_branch', css_class='form-control'),
            InlineCheckboxes('enable_flags'),
            HTML("<hr/>"),
            FormActions(
                Submit('addrelbranch', 'Add Release Branch'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def is_valid(self):
        return not len(self.errors) >= 1


class NewGraphRuleForm(forms.Form):
    """Add new graph rule"""
    rule_packages_choices = ()
    rule_langs_choices = ()
    rule_relbranch_choices = ()
    rule_tags_choices = ()

    rule_name = forms.CharField(
        label='Coverage Rule Name', help_text='Coverage Rule should be in slug form. '
                                              'Reports will be based on this rule.',
        required=True,
    )
    rule_relbranch = forms.ChoiceField(
        label='Release', choices=rule_relbranch_choices,
        help_text='Coverage will be generated for selected release based on branch mapping '
                  'of Platform and Build System.',
        required=True
    )
    tags_selection = forms.ChoiceField(
        label='Build Tags Selection', choices=[
            ('pick', 'Pick tags specific to package branch mapping'),
            ('select', 'Select and override tags')],
        initial='pick', widget=forms.RadioSelect, required=True,
        help_text="Either pick build tags associated with package branch mapping or choose tags."
    )
    rule_build_tags = TextArrayField(
        label='Build Tags', widget=forms.SelectMultiple, choices=rule_tags_choices,
        help_text="Selected build tags will be included in this rule.", required=False
    )
    rule_packages = TextArrayField(
        label='Packages', widget=forms.SelectMultiple, choices=rule_packages_choices,
        help_text="Selected packages will be included in this rule.", required=True
    )
    lang_selection = forms.ChoiceField(
        label='Languages Selection', choices=[
            ('pick', 'Pick release specific languages'),
            ('select', 'Select languages')],
        initial='pick', widget=forms.RadioSelect, required=True,
        help_text="Either pick language set associated with selected release or choose languages."
    )
    rule_visibility_public = forms.ChoiceField(
        label='Rule Visibility', choices=[
            ('public', 'Public'),
            ('private', 'Private')],
        initial='private', widget=forms.RadioSelect, required=True,
        help_text="Private rules will be visible only to logged in users."
    )
    rule_langs = TextArrayField(
        label='Languages', widget=forms.SelectMultiple, choices=rule_langs_choices,
        help_text="Selected languages will be included in this rule.", required=False
    )

    def __init__(self, *args, **kwargs):
        self.rule_packages_choices = kwargs.pop('packages')
        self.rule_langs_choices = kwargs.pop('languages')
        self.rule_relbranch_choices = kwargs.pop('branches')
        self.rule_tags_choices = kwargs.pop('tags')
        super(NewGraphRuleForm, self).__init__(*args, **kwargs)
        self.fields['rule_packages'].choices = self.rule_packages_choices
        self.fields['rule_langs'].choices = self.rule_langs_choices
        self.fields['rule_relbranch'].choices = self.rule_relbranch_choices
        self.fields['rule_build_tags'].choices = self.rule_tags_choices
        super(NewGraphRuleForm, self).full_clean()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.error_text_inline = True
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Field('rule_name', css_class="form-control", onkeyup="showRuleSlug()"),
            Field('rule_relbranch', css_class="selectpicker"),
            InlineRadios('tags_selection', id="tags_selection_id"),
            Field('rule_build_tags', css_class="selectpicker"),
            Field('rule_packages', css_class="selectpicker"),
            InlineRadios('lang_selection', id="lang_selection_id"),
            Field('rule_langs', css_class="selectpicker"),
            Field('rule_visibility_public', css_class="selectpicker"),
            HTML("<hr/>"),
            FormActions(
                Submit('addRule', 'Add Coverage Rule'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data['rule_visibility_public']
        if visibility == 'public':
            cleaned_data['rule_visibility_public'] = True
        elif visibility == 'private':
            cleaned_data['rule_visibility_public'] = False
        return cleaned_data

    def is_valid(self):
        return not len(self.errors) >= 1


class UpdateGraphRuleForm(forms.ModelForm):
    """Update Graph Rule form"""

    def __init__(self, *args, **kwargs):
        super(UpdateGraphRuleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = GraphRule
        fields = ['rule_name', 'rule_release_slug', 'rule_packages',
                  'rule_visibility_public', 'rule_languages', 'rule_build_tags']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('rule_name', css_class='form-control', readonly=True),
            Field('rule_release_slug', css_class='selectpicker'),
            Field('rule_packages', css_class='selectpicker'),
            Field('rule_languages', css_class='selectpicker'),
            Field('rule_visibility_public', css_class='selectpicker'),
            Field('rule_build_tags', css_class='selectpicker'),
            HTML("<hr/>"),
            FormActions(
                Submit('updateRule', 'Update Coverage Rule'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_rule_name(self):
        """Don't allow to override the value of 'rule_name' as it is readonly field"""
        rule_name = getattr(self.instance, 'rule_name', None)
        if rule_name:
            return rule_name
        else:
            return self.cleaned_data.get('rule_name', None)


class NewLanguageForm(forms.ModelForm):
    """Add new language form"""
    def __init__(self, *args, **kwargs):
        super(NewLanguageForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Language
        fields = '__all__'

    locale_id = forms.SlugField(label='Locale ID')
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('lang_name', css_class='form-control'),
            Field('locale_id', css_class='form-control'),
            Field('locale_script', css_class='form-control'),
            Field('locale_alias', css_class='form-control'),
            Field('lang_status', css_class='bootstrap-switch'),
            FormActions(
                Submit('addLanguage', 'Add Language'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )


class UpdateLanguageForm(forms.ModelForm):
    """Update language form"""
    def __init__(self, *args, **kwargs):
        super(UpdateLanguageForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Language
        fields = '__all__'

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('locale_id', css_class='form-control', readonly=True),
            Field('lang_name', css_class='form-control'),
            Field('locale_script', css_class='form-control'),
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
    """Language set form, for new language set and update language set"""
    class Meta:
        model = LanguageSet
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(LanguageSetForm, self).__init__(*args, **kwargs)
        inventory_manager = InventoryManager()
        self.fields['locale_ids'].choices = tuple([(locale.locale_id, locale.lang_name)
                                                   for locale in inventory_manager.get_locales()])

    lang_set_slug = forms.SlugField(label='Language Set SLUG')
    locale_ids = TextArrayField(label='Languages', widget=forms.SelectMultiple,)
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('lang_set_name', css_class='form-control'),
            Field('lang_set_slug', css_class='form-control'),
            Field('locale_ids', css_class='selectpicker'),
            Row(
                Field('lang_set_color', css_class='form-control'),
                FormActions(
                    Submit('addLanguageSet', 'Add Language Set'), Reset('reset', 'Reset', css_class='btn-danger')
                ),
                css_class='col-xs-3'
            ),
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        lang_set = cleaned_data['lang_set_name']
        cleaned_data['lang_set_slug'] = slugify(lang_set)
        return cleaned_data


class NewTransPlatformForm(forms.ModelForm):
    """Add new TransPlatform form"""
    def __init__(self, *args, **kwargs):
        super(NewTransPlatformForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Platform
        fields = ['engine_name', 'subject', 'api_url', 'platform_slug',
                  'server_status', 'ci_status', 'auth_login_id', 'auth_token_key']

    engine_name = forms.ChoiceField(
        choices=ENGINE_CHOICES, label="Platform Engine",
        help_text="Platform engine helps system to determine specific API/tasks."
    )
    platform_slug = forms.ChoiceField(
        choices=SLUG_CHOICES, label="Platform SLUG",
        help_text="Please identify SLUG carefully. Example: DMLSPUB should be for DamnedLies Public instance.",
    )
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('engine_name', css_class='selectpicker'),
            Field('subject', css_class='form-control'),
            Field('api_url', css_class='form-control'),
            Field('platform_slug', css_class='selectpicker'),
            Field('server_status', css_class='bootstrap-switch'),
            Field('auth_login_id', css_class='form-control'),
            Field('auth_token_key', css_class='form-control'),
            Field('ci_status', css_class='bootstrap-switch'),
            FormActions(
                Submit('addTransPlatform', 'Add Translation Platform'), Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_api_url(self):
        """Remove trailing slash if any"""
        api_url = self.cleaned_data.get('api_url')
        if api_url:
            return api_url if not api_url.endswith('/') else api_url.rstrip('/')
        else:
            return self.cleaned_data.get('api_url')


class UpdateTransPlatformForm(forms.ModelForm):
    """Update TransPlatform form"""
    def __init__(self, *args, **kwargs):
        super(UpdateTransPlatformForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Platform
        fields = ['engine_name', 'subject', 'api_url', 'platform_slug', 'server_status',
                  'auth_login_id', 'auth_token_key', 'token_expiry', 'ci_status']

    auth_token_key = forms.CharField(label="Auth Password/Token",
                                     widget=forms.PasswordInput(render_value=True),
                                     required=False)

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
            Field('token_expiry', css_class='form-control', readonly=True),
            Field('ci_status', css_class='bootstrap-switch'),
            HTML("<hr/>"),
            HTML("<h5 class='pull-right'>Run <span class='text-info'>Sync Translation Platforms</span>"
                 " in <span class='text-info'>Tasks</span> to update projects.</h5>"),
            FormActions(
                Submit('updateTransPlatform', 'Update Translation Platform'),
                Reset('reset', 'Reset', css_class='btn-danger')
            )
        )
    )

    def clean_engine_name(self):
        """Don't allow to override the value of 'engine_name' as it is readonly field"""
        engine_name = getattr(self.instance, 'engine_name', None)
        if engine_name:
            return engine_name
        else:
            return self.cleaned_data.get('engine_name')

    def clean_platform_slug(self):
        """Don't allow to override the value of 'platform_slug' as it is readonly field"""
        platform_slug = getattr(self.instance, 'platform_slug', None)
        if platform_slug:
            return platform_slug
        else:
            return self.cleaned_data.get('platform_slug')

    def clean_api_url(self):
        """Remove trailing slash if any"""
        api_url = getattr(self.instance, 'api_url', None)
        if api_url:
            return api_url if not api_url.endswith('/') else api_url.rstrip('/')
        else:
            return self.cleaned_data.get('api_url')


class PackagePipelineForm(forms.ModelForm):
    """Add Package CI Pipeline form"""

    ci_project_web_url = forms.URLField(
        label='CI Platform Project URL', required=True,
        help_text='CI Pipeline will be associated with this project.'
    )

    ci_pipeline_default_branch = forms.ChoiceField(required=False)
    ci_pipeline_auto_create_config = forms.BooleanField(
        required=False, initial=True, label='Auto Create Pipeline Configurations'
    )

    def __init__(self, *args, **kwargs):
        ci_platform_choices = kwargs.pop('ci_platform_choices')
        pkg_release_choices = kwargs.pop('pkg_release_choices')
        pkg_platform_branch_choices = kwargs.pop('pkg_platform_branch_choices')
        pkg_branch_display_name = kwargs.pop('pkg_branch_display_name')
        pkg_name, pkg_platform = kwargs.pop('package_name'), kwargs.pop('package_platform')
        super(PackagePipelineForm, self).__init__(*args, **kwargs)
        self.fields['ci_platform'].choices = ci_platform_choices
        self.fields['ci_release'].choices = pkg_release_choices
        self.fields['ci_pipeline_default_branch'].choices = \
            sorted(pkg_platform_branch_choices, key=lambda x: x[1])
        self.fields['ci_pipeline_default_branch'].label = f'Pipeline {pkg_branch_display_name}'
        self.fields['ci_pipeline_default_branch'].help_text = \
            f'This will be the default {pkg_branch_display_name.lower()}. ' \
            f'Resync {pkg_name} with {pkg_platform} for the latest.'

    class Meta:
        model = CIPipeline
        fields = ['ci_platform', 'ci_release', 'ci_push_job_template',
                  'ci_pull_job_template', 'ci_project_web_url']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('ci_platform', css_class='selectpicker'),
            Field('ci_release', css_class='selectpicker'),
            Field('ci_push_job_template', css_class='selectpicker'),
            Field('ci_pull_job_template', css_class='selectpicker'),
            Field('ci_pipeline_default_branch', css_class='selectpicker'),
            Field('ci_project_web_url', css_class='form-control'),
            PrependedText('ci_pipeline_auto_create_config', ''),
            FormActions(
                Submit('addCIPipeline', 'Add CI Pipeline'),
                Reset('reset', 'Reset', css_class='btn-danger'),
                HTML('<a class="pull-right btn btn-info" href="{% url "pipelines" %}">Pipelines</a>')
            )
        )
    )

    def clean_ci_project_web_url(self):
        """Clean CI Project Web URL"""
        if self.cleaned_data.get('ci_project_web_url'):
            parsed_url = urlparse(self.cleaned_data['ci_project_web_url'])
            return "{}://{}{}".format(parsed_url.scheme, parsed_url.netloc, parsed_url.path)
        return ""


class CreateCIPipelineForm(forms.ModelForm):
    """Add new CI Pipeline form"""

    ci_project_web_url = forms.URLField(
        label='CI Platform Project URL', required=True,
        help_text='CI Pipeline will be associated with this project.'
    )

    def __init__(self, *args, **kwargs):
        ci_platform_choices = kwargs.pop('ci_platform_choices')
        package_choices = kwargs.pop('package_choices')
        release_choices = kwargs.pop('release_choices')
        super(CreateCIPipelineForm, self).__init__(*args, **kwargs)
        self.fields['ci_platform'].choices = ci_platform_choices
        self.fields['ci_release'].choices = release_choices
        self.fields['ci_package'].choices = package_choices

    class Meta:
        model = CIPipeline
        fields = ['ci_package', 'ci_platform', 'ci_release', 'ci_push_job_template',
                  'ci_pull_job_template', 'ci_project_web_url']

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'dynamic-form'
    helper.layout = Layout(
        Div(
            Field('ci_package', css_class='selectpicker'),
            Field('ci_platform', css_class='selectpicker'),
            Field('ci_release', css_class='selectpicker'),
            Field('ci_push_job_template', css_class='selectpicker'),
            Field('ci_pull_job_template', css_class='selectpicker'),
            Field('ci_project_web_url', css_class='form-control'),
            FormActions(
                Submit('addCIPipeline', 'Add CI Pipeline'),
                Reset('reset', 'Reset', css_class='btn-danger'),
                HTML('<a class="pull-right btn btn-info" href="{% url "pipelines" %}">Return</a>')
            )
        )
    )

    def clean_ci_project_web_url(self):
        """Clean CI Project Web URL"""
        if self.cleaned_data.get('ci_project_web_url'):
            parsed_url = urlparse(self.cleaned_data['ci_project_web_url'])
            return "{}://{}{}".format(parsed_url.scheme, parsed_url.netloc, parsed_url.path)
        return ""
