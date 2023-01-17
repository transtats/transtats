# Jobs Framework
import os
from datetime import datetime
from subprocess import Popen, PIPE

from django.conf import settings

from dashboard.constants import GIT_PLATFORMS
from dashboard.managers import BaseManager


class JobCommandBase(BaseManager):

    double_underscore_delimiter = "__"

    def __init__(self):

        kwargs = {
            'sandbox_path': 'dashboard/sandbox/',
        }
        super(JobCommandBase, self).__init__(**kwargs)

    def _format_log_text(self, delimiter, text, text_prefix):
        log_text = ''
        if isinstance(text, str):
            log_text = text
        if isinstance(text, (list, tuple)):
            log_text = delimiter.join(text)
        if text_prefix:
            log_text = " :: " + text_prefix + delimiter + log_text
        return log_text

    def _log_task(self, log_f, subject, text, text_prefix=None):
        if ".log" not in log_f:
            raise Exception("Log file is not formatted.")
        with open(log_f, 'a+') as the_file:
            text_to_write = \
                '\n<b>' + subject + '</b> ...\n%s\n' % \
                                    self._format_log_text(" \n ", text, text_prefix)
            the_file.write(text_to_write)
        return {str(datetime.now()): '%s' % self._format_log_text(", ", text, text_prefix)}

    def _run_shell_cmd(self, command):
        process = Popen(command, stdout=PIPE, shell=True)
        while True:
            line = process.stdout.readline().rstrip()
            if not line:
                break
            yield line

    def find_dir(self, dirname, path):
        for root, dirs, files in os.walk(path):
            if root[len(path) + 1:].count(os.sep) < 2:
                if dirname in dirs:
                    return os.path.join(root, dirname)

    @property
    def github_user(self):
        github_user = settings.GITHUB_USER
        kwargs = {}
        kwargs.update(dict(no_cache_api=True))
        github_user_details = self.api_resources.user_details(
            GIT_PLATFORMS[0], instance_url='', **kwargs
        )
        if github_user_details and github_user_details.get("login"):
            github_user = github_user_details["login"]
        return github_user
