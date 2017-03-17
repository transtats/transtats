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

    def _format_stats_for_default_graphs(self, locale_sequence, stats_dict, desc):
        """
        Formats stats dict for graph-ready material
        """
        stats_for_graphs_dict = OrderedDict()

        stats_for_graphs_dict['pkg_desc'] = desc
        stats_for_graphs_dict['ticks'] = \
            [[i, lang] for i, lang in enumerate(locale_sequence.values(), 0)]

        stats_for_graphs_dict['graph_data'] = OrderedDict()
        for version, stats_lists in stats_dict.items():
            new_stats_list = []
            for stats_tuple in stats_lists:
                locale = stats_tuple[0].replace('-', '_') if ('-' in stats_tuple[0]) else stats_tuple[0]
                index = [i for i, locale_tuple in enumerate(list(locale_sequence), 0) if locale in locale_tuple]
                index.append(stats_tuple[1])
                new_stats_list.append(index)
            stats_for_graphs_dict['graph_data'][version] = new_stats_list

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
        # format trans_stats_list for graphs
        return self._format_stats_for_default_graphs(lang_id_name, stats_dict, pkg_desc)

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
