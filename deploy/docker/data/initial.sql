--
-- Data for Name: ts_locales; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('as_IN', 'Assamese', 'as', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('bn_IN', 'Bengali', 'bn', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('de_DE', 'German', 'de', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('es_ES', 'Spanish', 'es', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('fr_FR', 'French', 'fr', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('gu_IN', 'Gujarati', 'gu', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('it_IT', 'Italian', 'it', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('ja_JP', 'Japanese', 'ja', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('kn_IN', 'Kannada', 'kn', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('ko_KR', 'Korean', 'ko', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('ml_IN', 'Malayalam', 'ml', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('pa_IN', 'Punjabi', 'pa', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('pt_BR', 'Portuguese (Brazilian)', 'pt', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('ru_RU', 'Russian', 'ru', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('ta_IN', 'Tamil', 'ta', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('te_IN', 'Telugu', 'te', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('zh_CN', 'Chinese (Simplified)', 'zh-Hans', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('zh_TW', 'Chinese (Traditional)', 'zh-Hant', TRUE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('or_IN', 'Odia', 'or', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('mr_IN', 'Marathi', 'mr', FALSE);
INSERT INTO ts_locales (locale_id, lang_name, locale_alias, lang_status) VALUES ('hi_IN', 'Hindi', 'hi', FALSE);

--
-- Data for Name: ts_langset; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO ts_langset (lang_set_name, lang_set_slug, lang_set_color, locale_ids) VALUES ('Master Set', 'master-set', 'Grey', ARRAY['as_IN', 'bn_IN', 'de_DE', 'es_ES', 'fr_FR',
'gu_IN', 'it_IT', 'ja_JP', 'kn_IN', 'ko_KR', 'ml_IN', 'pa_IN', 'pt_BR', 'ru_RU', 'ta_IN', 'te_IN', 'zh_CN', 'zh_TW', 'or_IN', 'mr_IN', 'hi_IN']);
INSERT INTO ts_langset (lang_set_name, lang_set_slug, lang_set_color, locale_ids) VALUES ('All Enabled', 'all-enabled', 'LightSeaGreen', ARRAY['de_DE', 'es_ES', 'fr_FR', 'it_IT', 'ja_JP', 'ko_KR', 'pt_BR', 'ru_RU', 'zh_CN', 'zh_TW']);

--
-- Data for Name: ts_transplatforms; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO ts_transplatforms (engine_name, subject, api_url, platform_slug, server_status) VALUES ('zanata', 'public', 'https://translate.zanata.org', 'ZNTAPUB', TRUE);
INSERT INTO ts_transplatforms (engine_name, subject, api_url, platform_slug, server_status) VALUES ('zanata', 'fedora', 'https://fedora.zanata.org', 'ZNTAFED', TRUE);

--
-- Data for Name: ts_relstreams; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO ts_relstreams (relstream_name, relstream_slug, relstream_server, relstream_built, srcpkg_format, top_url, web_url, krb_service, auth_type, amqp_server, msgbus_exchange, major_milestones, relstream_phases, relstream_status)
VALUES ('Fedora', 'fedora', 'https://koji.fedoraproject.org/kojihub', 'koji', 'srpm', 'https://kojipkgs.fedoraproject.org', 'https://koji.fedoraproject.org/koji/', NULL, 'FAS', NULL, 'fedmsg',
ARRAY['Testing Phase', 'Alpha Release', 'String Freeze', 'Translation Deadline', 'Beta Release', 'Launch Phase', 'GA'], ARRAY['Planning', 'Development', 'Freeze', 'Release', 'Maintenance', 'Unsupported'], TRUE);
