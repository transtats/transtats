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
from dashboard.constants import (TRANSPLATFORM_ENGINES, CALENDAR_VERBS)


__all__ = ['parse_project_details_json', 'parse_ical_file',
           'COUNTRY_CODE_3to2_LETTERS', 'COUNTRY_CODE_2to3_LETTERS']


# Reverse of http://country.io/iso3.json
COUNTRY_CODE_3to2_LETTERS = {"BGD": "BD", "BEL": "BE", "BFA": "BF", "BGR": "BG", "BIH": "BA", "BRB": "BB",
                             "WLF": "WF", "BLM": "BL", "BMU": "BM", "BRN": "BN", "BOL": "BO", "BHR": "BH",
                             "BDI": "BI", "BEN": "BJ", "BTN": "BT", "JAM": "JM", "BVT": "BV", "BWA": "BW",
                             "WSM": "WS", "BES": "BQ", "BRA": "BR", "BHS": "BS", "JEY": "JE", "BLR": "BY",
                             "BLZ": "BZ", "RUS": "RU", "RWA": "RW", "SRB": "RS", "TLS": "TL", "REU": "RE",
                             "TKM": "TM", "TJK": "TJ", "ROU": "RO", "TKL": "TK", "GNB": "GW", "GUM": "GU",
                             "GTM": "GT", "SGS": "GS", "GRC": "GR", "GNQ": "GQ", "GLP": "GP", "JPN": "JP",
                             "GUY": "GY", "GGY": "GG", "GUF": "GF", "GEO": "GE", "GRD": "GD", "GBR": "GB",
                             "GAB": "GA", "SLV": "SV", "GIN": "GN", "GMB": "GM", "GRL": "GL", "GIB": "GI",
                             "GHA": "GH", "OMN": "OM", "TUN": "TN", "JOR": "JO", "HRV": "HR", "HTI": "HT",
                             "HUN": "HU", "HKG": "HK", "HND": "HN", "HMD": "HM", "VEN": "VE", "PRI": "PR",
                             "PSE": "PS", "PLW": "PW", "PRT": "PT", "SJM": "SJ", "PRY": "PY", "IRQ": "IQ",
                             "PAN": "PA", "PYF": "PF", "PNG": "PG", "PER": "PE", "PAK": "PK", "PHL": "PH",
                             "PCN": "PN", "POL": "PL", "SPM": "PM", "ZMB": "ZM", "ESH": "EH", "EST": "EE",
                             "EGY": "EG", "ZAF": "ZA", "ECU": "EC", "ITA": "IT", "VNM": "VN", "SLB": "SB",
                             "ETH": "ET", "SOM": "SO", "ZWE": "ZW", "SAU": "SA", "ESP": "ES", "ERI": "ER",
                             "MNE": "ME", "MDA": "MD", "MDG": "MG", "MAF": "MF", "MAR": "MA", "MCO": "MC",
                             "UZB": "UZ", "MMR": "MM", "MLI": "ML", "MAC": "MO", "MNG": "MN", "MHL": "MH",
                             "MKD": "MK", "MUS": "MU", "MLT": "MT", "MWI": "MW", "MDV": "MV", "MTQ": "MQ",
                             "MNP": "MP", "MSR": "MS", "MRT": "MR", "IMN": "IM", "UGA": "UG", "TZA": "TZ",
                             "MYS": "MY", "MEX": "MX", "ISR": "IL", "FRA": "FR", "IOT": "IO", "SHN": "SH",
                             "FIN": "FI", "FJI": "FJ", "FLK": "FK", "FSM": "FM", "FRO": "FO", "NIC": "NI",
                             "NLD": "NL", "NOR": "NO", "NAM": "NA", "VUT": "VU", "NCL": "NC", "NER": "NE",
                             "NFK": "NF", "NGA": "NG", "NZL": "NZ", "NPL": "NP", "NRU": "NR", "NIU": "NU",
                             "COK": "CK", "XKX": "XK", "CIV": "CI", "CHE": "CH", "COL": "CO", "CHN": "CN",
                             "CMR": "CM", "CHL": "CL", "CCK": "CC", "CAN": "CA", "COG": "CG", "CAF": "CF",
                             "COD": "CD", "CZE": "CZ", "CYP": "CY", "CXR": "CX", "CRI": "CR", "CUW": "CW",
                             "CPV": "CV", "CUB": "CU", "SWZ": "SZ", "SYR": "SY", "SXM": "SX", "KGZ": "KG",
                             "KEN": "KE", "SSD": "SS", "SUR": "SR", "KIR": "KI", "KHM": "KH", "KNA": "KN",
                             "COM": "KM", "STP": "ST", "SVK": "SK", "KOR": "KR", "SVN": "SI", "PRK": "KP",
                             "KWT": "KW", "SEN": "SN", "SMR": "SM", "SLE": "SL", "SYC": "SC", "KAZ": "KZ",
                             "CYM": "KY", "SGP": "SG", "SWE": "SE", "SDN": "SD", "DOM": "DO", "DMA": "DM",
                             "DJI": "DJ", "DNK": "DK", "VGB": "VG", "DEU": "DE", "YEM": "YE", "DZA": "DZ",
                             "USA": "US", "URY": "UY", "MYT": "YT", "UMI": "UM", "LBN": "LB", "LCA": "LC",
                             "LAO": "LA", "TUV": "TV", "TWN": "TW", "TTO": "TT", "TUR": "TR", "LKA": "LK",
                             "LIE": "LI", "LVA": "LV", "TON": "TO", "LTU": "LT", "LUX": "LU", "LBR": "LR",
                             "LSO": "LS", "THA": "TH", "ATF": "TF", "TGO": "TG", "TCD": "TD", "TCA": "TC",
                             "LBY": "LY", "VAT": "VA", "VCT": "VC", "ARE": "AE", "AND": "AD", "ATG": "AG",
                             "AFG": "AF", "AIA": "AI", "VIR": "VI", "ISL": "IS", "IRN": "IR", "ARM": "AM",
                             "ALB": "AL", "AGO": "AO", "ATA": "AQ", "ASM": "AS", "ARG": "AR", "AUS": "AU",
                             "AUT": "AT", "ABW": "AW", "IND": "IN", "ALA": "AX", "AZE": "AZ", "IRL": "IE",
                             "IDN": "ID", "UKR": "UA", "QAT": "QA", "MOZ": "MZ"}

# http://country.io/iso3.json
COUNTRY_CODE_2to3_LETTERS = {"BD": "BGD", "BE": "BEL", "BF": "BFA", "BG": "BGR", "BA": "BIH", "BB": "BRB",
                             "WF": "WLF", "BL": "BLM", "BM": "BMU", "BN": "BRN", "BO": "BOL", "BH": "BHR",
                             "BI": "BDI", "BJ": "BEN", "BT": "BTN", "JM": "JAM", "BV": "BVT", "BW": "BWA",
                             "WS": "WSM", "BQ": "BES", "BR": "BRA", "BS": "BHS", "JE": "JEY", "BY": "BLR",
                             "BZ": "BLZ", "RU": "RUS", "RW": "RWA", "RS": "SRB", "TL": "TLS", "RE": "REU",
                             "TM": "TKM", "TJ": "TJK", "RO": "ROU", "TK": "TKL", "GW": "GNB", "GU": "GUM",
                             "GT": "GTM", "GS": "SGS", "GR": "GRC", "GQ": "GNQ", "GP": "GLP", "JP": "JPN",
                             "GY": "GUY", "GG": "GGY", "GF": "GUF", "GE": "GEO", "GD": "GRD", "GB": "GBR",
                             "GA": "GAB", "SV": "SLV", "GN": "GIN", "GM": "GMB", "GL": "GRL", "GI": "GIB",
                             "GH": "GHA", "OM": "OMN", "TN": "TUN", "JO": "JOR", "HR": "HRV", "HT": "HTI",
                             "HU": "HUN", "HK": "HKG", "HN": "HND", "HM": "HMD", "VE": "VEN", "PR": "PRI",
                             "PS": "PSE", "PW": "PLW", "PT": "PRT", "SJ": "SJM", "PY": "PRY", "IQ": "IRQ",
                             "PA": "PAN", "PF": "PYF", "PG": "PNG", "PE": "PER", "PK": "PAK", "PH": "PHL",
                             "PN": "PCN", "PL": "POL", "PM": "SPM", "ZM": "ZMB", "EH": "ESH", "EE": "EST",
                             "EG": "EGY", "ZA": "ZAF", "EC": "ECU", "IT": "ITA", "VN": "VNM", "SB": "SLB",
                             "ET": "ETH", "SO": "SOM", "ZW": "ZWE", "SA": "SAU", "ES": "ESP", "ER": "ERI",
                             "ME": "MNE", "MD": "MDA", "MG": "MDG", "MF": "MAF", "MA": "MAR", "MC": "MCO",
                             "UZ": "UZB", "MM": "MMR", "ML": "MLI", "MO": "MAC", "MN": "MNG", "MH": "MHL",
                             "MK": "MKD", "MU": "MUS", "MT": "MLT", "MW": "MWI", "MV": "MDV", "MQ": "MTQ",
                             "MP": "MNP", "MS": "MSR", "MR": "MRT", "IM": "IMN", "UG": "UGA", "TZ": "TZA",
                             "MY": "MYS", "MX": "MEX", "IL": "ISR", "FR": "FRA", "IO": "IOT", "SH": "SHN",
                             "FI": "FIN", "FJ": "FJI", "FK": "FLK", "FM": "FSM", "FO": "FRO", "NI": "NIC",
                             "NL": "NLD", "NO": "NOR", "NA": "NAM", "VU": "VUT", "NC": "NCL", "NE": "NER",
                             "NF": "NFK", "NG": "NGA", "NZ": "NZL", "NP": "NPL", "NR": "NRU", "NU": "NIU",
                             "CK": "COK", "XK": "XKX", "CI": "CIV", "CH": "CHE", "CO": "COL", "CN": "CHN",
                             "CM": "CMR", "CL": "CHL", "CC": "CCK", "CA": "CAN", "CG": "COG", "CF": "CAF",
                             "CD": "COD", "CZ": "CZE", "CY": "CYP", "CX": "CXR", "CR": "CRI", "CW": "CUW",
                             "CV": "CPV", "CU": "CUB", "SZ": "SWZ", "SY": "SYR", "SX": "SXM", "KG": "KGZ",
                             "KE": "KEN", "SS": "SSD", "SR": "SUR", "KI": "KIR", "KH": "KHM", "KN": "KNA",
                             "KM": "COM", "ST": "STP", "SK": "SVK", "KR": "KOR", "SI": "SVN", "KP": "PRK",
                             "KW": "KWT", "SN": "SEN", "SM": "SMR", "SL": "SLE", "SC": "SYC", "KZ": "KAZ",
                             "KY": "CYM", "SG": "SGP", "SE": "SWE", "SD": "SDN", "DO": "DOM", "DM": "DMA",
                             "DJ": "DJI", "DK": "DNK", "VG": "VGB", "DE": "DEU", "YE": "YEM", "DZ": "DZA",
                             "US": "USA", "UY": "URY", "YT": "MYT", "UM": "UMI", "LB": "LBN", "LC": "LCA",
                             "LA": "LAO", "TV": "TUV", "TW": "TWN", "TT": "TTO", "TR": "TUR", "LK": "LKA",
                             "LI": "LIE", "LV": "LVA", "TO": "TON", "LT": "LTU", "LU": "LUX", "LR": "LBR",
                             "LS": "LSO", "TH": "THA", "TF": "ATF", "TG": "TGO", "TD": "TCD", "TC": "TCA",
                             "LY": "LBY", "VA": "VAT", "VC": "VCT", "AE": "ARE", "AD": "AND", "AG": "ATG",
                             "AF": "AFG", "AI": "AIA", "VI": "VIR", "IS": "ISL", "IR": "IRN", "AM": "ARM",
                             "AL": "ALB", "AO": "AGO", "AQ": "ATA", "AS": "ASM", "AR": "ARG", "AU": "AUS",
                             "AT": "AUT", "AW": "ABW", "IN": "IND", "AX": "ALA", "AZ": "AZE", "IE": "IRL",
                             "ID": "IDN", "UA": "UKR", "QA": "QAT", "MZ": "MOZ"}


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

    if {CALENDAR_VERBS[0], CALENDAR_VERBS[1]}.issubset(ical_content):
        EVENT_BEGIN_SYMBOL = CALENDAR_VERBS[0]
        EVENT_END_SYMBOL = CALENDAR_VERBS[1]
    elif {CALENDAR_VERBS[2], CALENDAR_VERBS[3]}.issubset(ical_content):
        EVENT_BEGIN_SYMBOL = CALENDAR_VERBS[2]
        EVENT_END_SYMBOL = CALENDAR_VERBS[3]

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
