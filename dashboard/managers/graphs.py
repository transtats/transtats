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

# Stats Graphs

# python
import json
import functools
from operator import itemgetter
from collections import Counter, OrderedDict

# third-party
from slugify import slugify

# django
from django.utils import timezone

# dashboard
from dashboard.constants import (
    RELSTREAM_SLUGS, WORKLOAD_HEADERS, BRANCH_MAPPING_KEYS
)
from dashboard.managers import BaseManager
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.managers.packages import PackagesManager, PackageBranchMapping
from dashboard.models import GraphRule, Report


__all__ = ['GraphManager', 'ReportsManager']


class GraphManager(BaseManager):
    """
    Manage graph representations
    """

    package_manager = PackagesManager()
    branch_manager = ReleaseBranchManager()

    def get_graph_rules(self, graph_rule=None, only_active=None):
        """
        Fetch graph rules from db
        :return: resultset
        """
        filter_kwargs = {}
        if graph_rule:
            filter_kwargs.update(dict(rule_name=graph_rule))
        if only_active:
            filter_kwargs.update(dict(rule_status=True))

        rules = None
        try:
            rules = GraphRule.objects.filter(**filter_kwargs).order_by('rule_name')
        except:
            # log event, passing for now
            pass
        return rules

    def slugify_graph_rule_name(self, suggested_name):
        try:
            return slugify(suggested_name)
        except:
            # log even, passing for now
            return False

    def validate_package_branch_participation(self, relbranch, packages):
        """
        This validates that packages belong to relbranch or not
        :param relbranch: release branch
        :param packages: list of packages
        :return: list of packages that DO NOT belong
        """
        if not relbranch and not packages:
            return
        pkg_not_participate = []
        for package in packages:
            relbranches = PackageBranchMapping(package).release_branches
            if relbranch not in relbranches:
                pkg_not_participate.append(package)
        return pkg_not_participate

    def validate_tags_product_participation(self, release_slug, tags):
        """
        This validates that tag belongs to release
        :param release_slug: Release Slug
        :param tags: Build Tags
        :return: List of tags that do not belong
        """
        if not release_slug and not tags:
            return
        tags_not_participate = []

        q_release = self.branch_manager.get_release_branches(relbranch=release_slug)
        if q_release:
            release = q_release.get()
            release_build_tags = release.product_slug.product_build_tags
            for tag in tags:
                if tag not in release_build_tags:
                    tags_not_participate.append(tag)
        return tags_not_participate

    def add_graph_rule(self, **kwargs):
        """
        Save graph rule in db
        :param kwargs: dict
        :return: boolean
        """
        if not kwargs.get('rule_name'):
            return

        if not kwargs.get('rule_relbranch'):
            return

        relbranch_slug = kwargs.get('rule_relbranch')
        release_branch = \
            self.branch_manager.get_release_branches(relbranch=relbranch_slug)

        if kwargs.get('tags_selection') == "pick" and not kwargs.get('rule_build_tags'):
            release_packages = \
                self.package_manager.get_relbranch_specific_pkgs(
                    relbranch_slug, fields=['release_branch_mapping']
                )

            package_tags = [package.release_branch_mapping_json[relbranch_slug][BRANCH_MAPPING_KEYS[2]]
                            for package in release_packages if package.release_branch_mapping_json and
                            package.release_branch_mapping_json.get(relbranch_slug, {}).get(BRANCH_MAPPING_KEYS[2])]
            if package_tags:
                kwargs['rule_build_tags'] = list(set(package_tags))
            else:
                return False

        if kwargs.get('lang_selection') == "pick" and not kwargs.get('rule_langs'):
            relbranch_lang_set = self.branch_manager.get_release_branches(
                relbranch=relbranch_slug, fields=['language_set_slug']
            ).first()
            locales = relbranch_lang_set.language_set_slug.locale_ids
            if locales:
                kwargs['rule_languages'] = locales
            else:
                return False
        elif kwargs.get('rule_langs'):
            kwargs['rule_languages'] = kwargs.pop('rule_langs')

        filters = ['tags_selection', 'lang_selection', 'rule_langs', 'rule_relbranch']
        [kwargs.pop(i) for i in filters if i in kwargs]

        try:
            kwargs['rule_release_slug'] = release_branch.get()
            kwargs['created_on'] = timezone.now()
            kwargs['rule_status'] = True
            new_rule = GraphRule(**kwargs)
            new_rule.save()
        except:
            # log event, pass for now
            # todo implement error msg handling
            return False
        else:
            return True

    def _normalize_stats(self, stats_nested_list, index_list):
        """
        Normalize stats for a locale index and picks higher value
        """
        temp_index_list = []
        temp_stat_list = []
        for index, stat in stats_nested_list:
            if index not in temp_index_list:
                temp_index_list.append(index)
                temp_stat_list.append(stat)
            else:
                last_stat = temp_stat_list.pop(len(temp_stat_list) - 1)
                temp_stat_list.append(last_stat) \
                    if last_stat > stat else temp_stat_list.append(stat)
        expected_stats_list = list(zip(temp_index_list, temp_stat_list))
        if len(index_list) > len(expected_stats_list):
            expected_stats_dict = dict((k[0], k[1:]) for k in expected_stats_list)
            temp_patched_stats_list = []
            for index in index_list:
                temp_patched_stats_list.append([index, expected_stats_dict.get(index, [0.0])[0]])
            expected_stats_list = temp_patched_stats_list
        return expected_stats_list

    def _format_stats_for_default_graphs(self, locale_sequence, stats_dict, desc, prepend_source=False):
        """
        Formats stats dict for graph-ready material
        - sorting and normalization
        """
        stats_for_graphs_dict = OrderedDict()
        stats_for_graphs_dict['pkg_desc'] = desc
        stats_for_graphs_dict['ticks'] = \
            [[i, lang] for i, lang in enumerate(locale_sequence.values(), 0)]
        indexes = [index for index, lang in stats_for_graphs_dict['ticks']]

        graph_data_dict = {}
        for version, stats_lists in stats_dict.items():
            new_stats_list = []
            for stats_tuple in stats_lists:
                index = [i for i, locale_tuple in enumerate(list(locale_sequence), 0)
                         if (stats_tuple[0] in locale_tuple) or
                         (stats_tuple[0].replace('-', '_') in locale_tuple) or
                         (stats_tuple[0].replace('_', '-') in locale_tuple)]
                if index:
                    index.append(stats_tuple[1] or 0.0)
                    new_stats_list.append(index)
                if prepend_source:
                    if stats_tuple[0] == 'source' and stats_tuple[1] not in version.lower():
                        version = "{0} - {1}".format(stats_tuple[1], version)
            normalized_stats = self._normalize_stats(sorted(new_stats_list), indexes)
            if len(list(filter(lambda x: x[1] > 0.0, normalized_stats))) > 0:
                graph_data_dict[version] = normalized_stats
        stats_for_graphs_dict['graph_data'] = OrderedDict(sorted(graph_data_dict.items()))
        return stats_for_graphs_dict

    def get_trans_stats_by_package(self, package, prepend_source=False):
        """
        formats stats of a package for all enabled languages
        :param package: str
        :param prepend_source: boolean
        :return: Graph data for "Package-wise" view: dict
        """
        if not package:
            return {}
        lang_id_name, stats_dict, pkg_desc = self.package_manager.get_trans_stats(package)
        # format trans_stats_list for graphs
        return self._format_stats_for_default_graphs(lang_id_name, stats_dict, pkg_desc, prepend_source)

    def _format_stats_for_lang_wise_graphs(self, input_locale, locale_sequence, stats_dict, desc):
        """
        Formats stats dict for bar graph-ready material
        """
        stats_for_graphs_dict = OrderedDict()
        stats_branches = list(stats_dict.keys())
        stats_for_graphs_dict['pkg_desc'] = desc

        stats_for_graphs_dict['ticks'] = \
            [[i, version] for i, version in enumerate(stats_branches, 0)]

        stats_for_graphs_dict['graph_data'] = []
        for version, stats_lists in stats_dict.items():
            index = stats_branches.index(version)
            required_stat = 0.0
            for locale_tuple in list(locale_sequence.keys()):
                if input_locale in locale_tuple:
                    locale, alias = locale_tuple
                    expected_stat = [stat for lang, stat in stats_lists
                                     if lang.replace('-', '_') == locale or lang.replace('-', '_') == alias]
                    required_stat = expected_stat[0] if expected_stat and len(expected_stat) > 0 else 0.0
            stats_for_graphs_dict['graph_data'].append([required_stat, index])

        return stats_for_graphs_dict

    def get_stats_by_pkg_per_lang(self, package, locale):
        """
        formats stats of a package for given locale
        :param package: str
        :param locale: str
        :return: Graph data for "Language-wise" view: dict
        """
        if not package and not locale:
            return {}
        lang_id_name, stats_dict, pkg_desc = self.package_manager.get_trans_stats(package)
        # format stats for lang-wise graph
        return self._format_stats_for_lang_wise_graphs(locale, lang_id_name, stats_dict, pkg_desc)

    def _format_stats_for_custom_graphs(self, rel_branch, languages, stats_dict):
        """
        Formats stats dict for graph-ready material
        """
        stats_for_graphs_dict = OrderedDict()
        stats_for_graphs_dict['branch'] = rel_branch
        stats_for_graphs_dict['ticks'] = \
            [[i, package] for i, package in enumerate(stats_dict.keys(), 0)]

        stats_for_graphs_dict['graph_data'] = []
        for language in languages:
            stats = []
            graph_lang_stats_dict = OrderedDict()
            graph_lang_stats_dict['label'] = language
            for lang_stat in stats_dict.values():
                stats.append(lang_stat.get(language))
            graph_lang_stats_dict['data'] = \
                [[i, stat] for i, stat in enumerate(stats, 0)]
            stats_for_graphs_dict['graph_data'].append(graph_lang_stats_dict)
        return stats_for_graphs_dict

    def get_trans_stats_by_rule(self, graph_rule):
        """
        formats stats of a graph rule
        :param: graph_rule: str
        :return: Graph data for "Rule-wise" view: dict
        """
        if not graph_rule:
            return {}
        rule = self.get_graph_rules(graph_rule=graph_rule).get()
        graph_rule_branch = rule.rule_release_slug.release_slug
        release_branch = self.branch_manager.get_release_branches(
            relbranch=graph_rule_branch, fields=['release_name']
        ).get().release_name
        packages = rule.rule_packages
        exclude_packages = []
        rule_locales = rule.rule_languages

        trans_stats_dict_set = OrderedDict()
        languages_list = []
        for package in packages:
            lang_id_name, package_stats = self.package_manager.get_trans_stats(
                package, apply_branch_mapping=True
            )[0:2]
            relbranch_stats = {}
            if graph_rule_branch in package_stats:
                relbranch_stats.update(package_stats.get(graph_rule_branch))
            elif 'master' in package_stats and package_stats.get('master'):
                relbranch_stats.update(package_stats.get('master'))
            elif 'default' in package_stats and package_stats.get('default'):
                relbranch_stats.update(package_stats.get('default'))
            else:
                exclude_packages.append(package)
            # filter locale_tuple for required locales
            required_locales = []
            for locale_tuple, lang in lang_id_name.items():
                rule_locale = [rule_locale for rule_locale in rule_locales if rule_locale in locale_tuple]
                if rule_locale:
                    required_locales.append((locale_tuple, lang))
            # set stat for filtered_locale_tuple checking with both locale and alias
            lang_stats = OrderedDict()
            for locale, stat in relbranch_stats.items():
                locale = locale.replace('-', '_') if '-' in locale else locale
                for locale_tuple, lang in required_locales:
                    if locale in locale_tuple:
                        lang_stats[lang] = stat
            languages_list = lang_stats.keys()
            trans_stats_dict_set[package] = lang_stats
        # this is to prevent any breaking in graphs
        for ex_package in exclude_packages:
            trans_stats_dict_set.pop(ex_package)

        # here trans_stats_dict_set would contain {'package': {'language': stat}}
        # now, lets format trans_stats_list for graphs
        return self._format_stats_for_custom_graphs(release_branch, languages_list, trans_stats_dict_set)

    def _consolidate_branch_specific_stats(self, packages_stats_dict):
        """
        Sum up stats per language
        """
        temp_stats_dict = {}
        pkgs_stats_list = list(packages_stats_dict.values())
        pkgs_length = len(pkgs_stats_list)
        for pkg_stats in pkgs_stats_list:
            for pkg_stat in pkg_stats:
                if pkg_stat[0] not in temp_stats_dict:
                    temp_stats_dict[pkg_stat[0]] = pkg_stat[1]
                else:
                    temp_stats_dict[pkg_stat[0]] += pkg_stat[1]
        # Reverse stats to depict how much is left
        return sorted([(i, 100 - int(j / pkgs_length)) for i, j in temp_stats_dict.items()])

    def _format_data_for_pie_chart(self, consolidated_stats, lang_options):
        """
        Takes consolidated stats and formats for pie chart
        """
        formatted_stats = []
        formatted_langs = []
        for lang, stat in consolidated_stats:
            formatted_stats.append({'label': lang, 'data': stat})
        for locale, language in lang_options:
            formatted_langs.append({'value': locale, 'text': language})
        return {'graph_data': formatted_stats,
                'select_options': sorted(formatted_langs, key=itemgetter('text'))}

    def _get_branch_specific_pkgs_stats(self, relbranch):
        """
        Generates translation stats of all packages in all langs of attached lang-set
        """
        specific_pkgs = [package.package_name for package in
                         self.package_manager.get_relbranch_specific_pkgs(relbranch, ['package_name'])]
        all_pkgs_stats_dict = OrderedDict()
        for pkg in specific_pkgs:
            pkg_lang_stats = []
            locale_seq, trans_stats_dict, pkg_desc = \
                self.package_manager.get_trans_stats(pkg, apply_branch_mapping=True, specify_branch=relbranch)
            t_stats = self._format_stats_for_default_graphs(locale_seq, trans_stats_dict, pkg_desc)
            branch_stats = t_stats.get('graph_data').get(relbranch)
            langs = t_stats.get('ticks')
            if branch_stats and langs:
                pkg_lang_stats.extend(list(zip([lang[1] for lang in langs], [stat[1] for stat in branch_stats])))
            all_pkgs_stats_dict[pkg] = pkg_lang_stats
        return all_pkgs_stats_dict

    def get_workload_graph_data(self, release_branch):
        """
        Build or generates workload graph data
        """
        consolidated_stats = self._consolidate_branch_specific_stats(
            self._get_branch_specific_pkgs_stats(release_branch)
        )
        # get branch specific languages for select option
        locale_lang_tuple = self.package_manager.get_locale_lang_tuple(
            locales=self.package_manager.get_relbranch_locales(release_branch)
        )
        return self._format_data_for_pie_chart(consolidated_stats, locale_lang_tuple)

    def _process_workload_combined_view(self, packages_stats_dict, headers):
        stats_summary_dict = OrderedDict()
        for package, locale_stats in packages_stats_dict.items():
            reduced_stats = {}
            try:
                reduced_stats = functools.reduce(
                    lambda x, y: dict(Counter(x) + Counter(y)), list(locale_stats.values())
                )
            except Exception as e:
                # log error, pass for now
                pass
            if not reduced_stats:
                for field in headers:
                    reduced_stats[field] = 0
            try:
                if not reduced_stats.get('Untranslated'):
                    reduced_stats['Untranslated'] = 0
                reduced_stats[headers[3]] = \
                    (reduced_stats['Untranslated'] /
                     reduced_stats.get('Total', 0) * 100)
            except ZeroDivisionError:
                # log error, pass for now
                pass
            stats_summary_dict[package] = reduced_stats
        return stats_summary_dict

    def get_workload_estimate(self, release_branch, locale=None):
        """
        Build list of packages with translation workload for a given branch
        """
        headers = WORKLOAD_HEADERS
        pkg_stats = self.package_manager.get_release_specific_package_stats(
            release_branch=release_branch)

        required_stats_dict = {}
        if not locale:
            required_stats_dict = self._process_workload_combined_view(pkg_stats, headers)
        elif isinstance(locale, str):
            for pkg, locale_stat in pkg_stats.items():
                required_stats_dict[pkg] = locale_stat.get(locale) or {header: 0 for header in headers}
        return headers, OrderedDict(sorted(
            required_stats_dict.items(), key=lambda x: x[1]['Remaining'], reverse=True
        ))

    def get_workload_combined(self, release_branch):
        """
        Build list of packages with translation workload for a given branch in all languages
        """
        return self.get_workload_estimate(release_branch)

    def get_workload_detailed(self, release_branch):
        """
        Build translation workload percentage for a given branch in all languages
        """
        relbranch_packages_stats = self._get_branch_specific_pkgs_stats(release_branch)
        locale_lang_tuple = self.package_manager.get_locale_lang_tuple(
            locales=self.package_manager.get_relbranch_locales(release_branch)
        )
        headers = sorted([lang for locale, lang in locale_lang_tuple])
        # Format data to fill table
        workload_combined = OrderedDict()
        for package, lang_stats in relbranch_packages_stats.items():
            temp_stat_list = []
            for lang_stat_tuple in lang_stats:
                temp_stat_list.insert(headers.index(lang_stat_tuple[0]), lang_stat_tuple[1])
            # flag incorrect branch mapping
            if len([i for i in temp_stat_list if i == 0]) == len(temp_stat_list):
                package += "*"
            if temp_stat_list:
                workload_combined[package] = temp_stat_list
        return headers, OrderedDict(sorted(workload_combined.items()))

    def get_workload_combined_detailed(self, release_branch):
        """
        Build translation workload for a given branch in all langs for all pkgs
        :param release_branch: str
        :return: dict
        """
        if not isinstance(release_branch, str):
            return {}
        locale_lang_tuple = self.package_manager.get_locale_lang_tuple(
            locales=self.package_manager.get_relbranch_locales(release_branch)
        )
        workload_combined_detailed = {}
        for locale, lang in locale_lang_tuple:
            workload_combined_detailed[lang] = \
                self.get_workload_estimate(release_branch, locale=locale)[1]
        return workload_combined_detailed

    def get_threshold_based(self, release_branch, threshold=70):
        """
        Build language list those have fulfilled given threshold
        :param release_branch: str
        :param threshold: translation %age margin: int
        :return: dict
        """

        consolidated_stats = self._consolidate_branch_specific_stats(
            self._get_branch_specific_pkgs_stats(release_branch)
        )
        # Reverse the stats to have - what has been covered
        consolidated_stats_reversed = [(lang, 100 - stat) for lang, stat in consolidated_stats]
        filtered_stats = list(filter(lambda elem: elem[1] > threshold, consolidated_stats_reversed))
        headers = ['Languages', 'Translation Complete %age']

        locale_lang_tuple = self.package_manager.get_locale_lang_tuple(
            locales=self.package_manager.get_relbranch_locales(release_branch)
        )
        lang_locale_dict = {v: k for k, v in dict(locale_lang_tuple).items()}

        return headers, filtered_stats, lang_locale_dict


class ReportsManager(GraphManager):
    """
    Manage Reports Generations
    """

    package_manager = PackagesManager()

    def get_reports(self, report_subject):
        """
        Fetch reports from db
        :return: Queryset
        """
        filter_kwargs = {}
        if report_subject:
            filter_kwargs.update(dict(report_subject=report_subject))

        reports = None
        try:
            reports = Report.objects.filter(**filter_kwargs)
        except Exception as e:
            self.app_logger(
                'ERROR', "Reports could not be fetched, details: " + str(e))
        return reports

    def create_or_update_report(self, **kwargs):
        """
        Creates or Updates a report
        :param kwargs: dict
        :return: boolean
        """
        if not kwargs.get('subject') and not kwargs.get('report_json'):
            return
        default_params = {}
        match_params = {
            'report_subject': kwargs['subject']
        }
        default_params.update(match_params)
        default_params['report_json_str'] = json.dumps(kwargs['report_json'])
        default_params['report_updated'] = timezone.now()
        try:
            Report.objects.update_or_create(
                report_subject=kwargs['subject'], defaults=default_params
            )
        except Exception as e:
            # log error
            return False
        else:
            return True

    def _filter_disabled_languages(self, lang_stats_dict):
        active_locales = self.package_manager.get_locales(only_active=True)
        active_languages = [locale.lang_name for locale in active_locales]
        return {k: v for k, v in lang_stats_dict.items() if k in active_languages}

    def analyse_releases_status(self):
        """
        Summarize Releases Status
        """
        relbranches = self.branch_manager.get_relbranch_name_slug_tuple()
        relbranch_report = {}
        for branch_slug, branch_name in relbranches:
            relbranch_report[branch_name] = {}
            relbranch_report[branch_name]['slug'] = branch_slug
            stats_estimate = self.get_workload_estimate(branch_slug)
            untranslated_messages = \
                [stats.get('Untranslated') for pkg, stats in stats_estimate[1].items()]
            if untranslated_messages:
                packages_need_attention = (len(untranslated_messages) - untranslated_messages.count(0)) or 0
                relbranch_report[branch_name]['packages_need_attention'] = packages_need_attention
                total_untranslated_msgs = (functools.reduce((lambda x, y: x + y), untranslated_messages)) or 0
                relbranch_report[branch_name]['total_untranslated_msgs'] = total_untranslated_msgs
                lang_stats_report = self._filter_disabled_languages(
                    self.get_workload_combined_detailed(branch_slug)
                )
                relbranch_report[branch_name]['languages'] = {}
                for lang, pkg_stats in lang_stats_report.items():
                    untranslated_msgs = []
                    untranslated_msgs.extend(
                        [stats.get('Untranslated') for pkg, stats in pkg_stats.items()]
                    )
                    total_untranslated_msgs = (functools.reduce((lambda x, y: x + y), untranslated_msgs)) or 0
                    relbranch_report[branch_name]['languages'][lang] = total_untranslated_msgs
        if self.create_or_update_report(**{
            'subject': 'releases', 'report_json': relbranch_report
        }):
            return OrderedDict(sorted(relbranch_report.items(), reverse=True))
        return False

    def analyse_packages_status(self):
        """
        Summarize Packages Status
        """
        all_packages = self.package_manager.get_packages(pkg_params=[
            'package_name', 'products', 'details_json_last_updated', 'stats_diff',
            'release_branch_mapping', 'platform_last_updated', 'upstream_last_updated'
        ])
        pkg_tracking_for_RHEL = all_packages.filter(products__icontains=RELSTREAM_SLUGS[0]).count()
        pkg_tracking_for_fedora = all_packages.filter(products__icontains=RELSTREAM_SLUGS[1]).count()
        pkg_details_week_old = all_packages.filter(
            details_json_last_updated__lte=timezone.now() - timezone.timedelta(days=7)).count()
        pkg_transtats_week_old = all_packages.filter(
            platform_last_updated__lte=timezone.now() - timezone.timedelta(days=7)).count()
        pkg_upstream_week_old = all_packages.filter(
            upstream_last_updated__lte=timezone.now() - timezone.timedelta(days=7)).count()
        relbranches = self.branch_manager.get_relbranch_name_slug_tuple()
        pkg_improper_branch_mapping = 0
        pkg_with_stats_diff = 0
        if relbranches and len(relbranches) > 0:
            relbranch_slugs = sorted([slug for slug, name in relbranches], reverse=True)
            pkgs_improper_branch_mapping = [i for i in all_packages
                                            if not i.release_branch_mapping_json.get(relbranch_slugs[0])]
            pkg_improper_branch_mapping = len(pkgs_improper_branch_mapping)
            pkg_with_stats_diff = list(set([i.package_name for i in all_packages
                                            for y in relbranch_slugs if i.stats_diff_json.get(y)]))

        package_report = {
            RELSTREAM_SLUGS[0]: pkg_tracking_for_RHEL or 0,
            RELSTREAM_SLUGS[1]: pkg_tracking_for_fedora or 0,
            'pkg_details_week_old': pkg_details_week_old or 0,
            'pkg_transtats_week_old': pkg_transtats_week_old or 0,
            'pkg_upstream_week_old': pkg_upstream_week_old or 0,
            'pkg_improper_branch_mapping': pkg_improper_branch_mapping or 0,
            'pkg_with_stats_diff': pkg_with_stats_diff or [],
            'pkg_having_stats_diff': len(pkg_with_stats_diff) or 0
        }
        if self.create_or_update_report(**{
            'subject': 'packages', 'report_json': package_report
        }):
            return package_report
        return False
