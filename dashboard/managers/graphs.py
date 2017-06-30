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
from operator import itemgetter
from collections import OrderedDict

# third-party
from slugify import slugify

# django
from django.utils import timezone

# dashboard
from dashboard.managers.base import BaseManager
from dashboard.managers.inventory import (
    PackagesManager, ReleaseBranchManager, PackageBranchMapping
)
from dashboard.models import GraphRules


__all__ = ['GraphManager']


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
            rules = GraphRules.objects.filter(**filter_kwargs).order_by('rule_name')
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

    def add_graph_rule(self, **kwargs):
        """
        Save graph rule in db
        :param kwargs: dict
        :return: boolean
        """
        if kwargs.get('lang_selection') == "pick" and not kwargs.get('rule_langs'):
            relbranch_slug = kwargs.get('rule_relbranch')
            relbranch_lang_set = self.branch_manager.get_release_branches(
                relbranch=relbranch_slug, fields=['lang_set']
            ).first()
            locales = self.branch_manager.get_langset(
                relbranch_lang_set.lang_set, fields=['locale_ids']
            ).locale_ids
            if locales:
                kwargs['rule_langs'] = locales
            else:
                return False

        if not (kwargs['rule_name']):
            return
        try:
            kwargs.pop('lang_selection')
            kwargs['created_on'] = timezone.now()
            kwargs['rule_status'] = True
            new_rule = GraphRules(**kwargs)
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

    def _format_stats_for_default_graphs(self, locale_sequence, stats_dict, desc):
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
                         (stats_tuple[0].replace('-', '_') in locale_tuple)]
                if index:
                    index.append(stats_tuple[1] or 0.0)
                    new_stats_list.append(index)
            graph_data_dict[version] = self._normalize_stats(
                sorted(new_stats_list), indexes
            )
        stats_for_graphs_dict['graph_data'] = OrderedDict(sorted(graph_data_dict.items()))
        return stats_for_graphs_dict

    def get_trans_stats_by_package(self, package):
        """
        formats stats of a package for all enabled languages
        :param package: str
        :return: Graph data for "Package-wise" view: dict
        """
        if not package:
            return {}
        lang_id_name, stats_dict, pkg_desc = self.package_manager.get_trans_stats(package)
        upstream_stats = self.package_manager.get_upstream_stats(package)
        if upstream_stats:
            stats_dict['Upstream'] = upstream_stats
        # format trans_stats_list for graphs
        return self._format_stats_for_default_graphs(lang_id_name, stats_dict, pkg_desc)

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
        graph_rule_branch = rule.rule_relbranch
        release_branch = self.branch_manager.get_release_branches(
            relbranch=graph_rule_branch, fields=['relbranch_name']
        ).get().relbranch_name
        packages = rule.rule_packages
        exclude_packages = []
        rule_locales = rule.rule_langs

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

    def _process_workload_combined_view(self, packages, stats_dict, fields):
        """
        Process packages stats to sum-up all locales and find avg
        """
        stats_summary_dict = OrderedDict()
        fields_dict = OrderedDict([(field, 0) for field in fields])
        [stats_summary_dict.update({package: fields_dict.copy()}) for package in packages]
        if not isinstance(stats_dict, dict):
            return {}
        forloop_counter = 0
        for __, stat_dict in stats_dict.items():
            forloop_counter += 1
            for pkg, detail_stat in stat_dict.items():
                for field in fields:
                    stats_summary_dict[pkg][field] += detail_stat.get(field, 0)
        for package, detail_stats_dict in stats_summary_dict.items():
            try:
                stats_summary_dict[package][fields[3]] = \
                    (detail_stats_dict.get('Untranslated', 0) /
                     detail_stats_dict.get('Total', 0) * 100)
            except ZeroDivisionError:
                # log error, pass for now
                pass
        return stats_summary_dict

    def get_workload_estimate(self, release_branch, locale=None):
        """
        Build list of packages with translation workload for a given branch
        """
        specific_locale_present = True if locale else False
        relbranch_pkgs_stats_dict = self._get_branch_specific_pkgs_stats(release_branch)
        relbranch_pkgs = sorted(list(relbranch_pkgs_stats_dict.keys()))

        locales = self.package_manager.get_relbranch_locales(release_branch) \
            if not specific_locale_present else [locale]
        required_stats = OrderedDict()

        HEADERS = ('Total', 'Translated', 'Untranslated', 'Remaining')

        for locale in locales:
            required_stats[locale] = OrderedDict()
            locale_alias = self.package_manager.get_locale_alias(locale)
            for package in relbranch_pkgs:
                pkg_branch_stats = PackageBranchMapping(package).branch_stats(release_branch)
                for stat in pkg_branch_stats.get('stats', []):
                    locale_found = stat.get('locale')
                    if (locale_found in locale or locale_found in locale_alias or
                            locale_found.replace('-', '_') in locale or
                            locale_found.replace('-', '_') in locale_alias):
                        temp_stat_field = OrderedDict()
                        temp_stat_field['Total'] = stat.get('total', 0)
                        temp_stat_field['Translated'] = stat.get('translated', 0)
                        temp_stat_field['Untranslated'] = stat.get('untranslated', 0)
                        remaining = 0
                        try:
                            remaining = (stat.get('untranslated') / stat.get('total')) * 100
                        except ZeroDivisionError:
                            # log error, pass for now
                            pass
                        temp_stat_field['Remaining'] = remaining
                        required_stats[locale][package] = temp_stat_field

        required_stats_dict = required_stats.get(locale, {}) \
            if specific_locale_present else \
            self._process_workload_combined_view(relbranch_pkgs, required_stats, HEADERS)
        return HEADERS, OrderedDict(sorted(
            required_stats_dict.items(), key=lambda x: x[1]['Remaining'], reverse=True
        ))

    def get_workload_combined(self, release_branch):
        """
        Build list of packages with translation workload for a given branch in all languages
        """
        return self.get_workload_estimate(release_branch)

    def get_workload_detailed(self, release_branch):
        """
        Build list of packages with translation workload for a given branch in all languages
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
                temp_stat_list.insert(headers.index(lang_stat_tuple[0]), 100 - lang_stat_tuple[1])
            # flag incorrect branch mapping
            if len([i for i in temp_stat_list if i == 100]) == len(temp_stat_list):
                package += "*"
            workload_combined[package] = temp_stat_list
        return headers, OrderedDict(sorted(workload_combined.items()))
