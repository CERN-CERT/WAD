from __future__ import absolute_import, division, print_function, unicode_literals
import six

from _ssl import SSLError
import copy
import logging
import socket
import re

from wad import tools
from wad.clues import Clues

re_meta = re.compile('<meta[^>]+name\s*=\s*["\']([^"\']*)["\'][^>]+content\s*=\s*["\']([^"\']*)', re.IGNORECASE)
re_script = re.compile('<script[^>]+src\s*=\s*["\']([^"\']*)', re.IGNORECASE)

TIMEOUT = 3


class Detector(object):
    def __init__(self):
        self.apps, self.categories = Clues.get_clues()

    def detect(self, url, limit=None, exclude=None, timeout=TIMEOUT):
        logging.info("- %s", url)

        findings = []
        original_url = url

        if not self.expected_url(url, limit, exclude):
            return {}

        try:
            page = tools.urlopen(url, timeout=timeout)
            url = page.geturl()
        except (six.moves.urllib.error.URLError, six.moves.http_client.HTTPException) as e:
            # a network problem? page unavailable? wrong URL?
            logging.warning("Error opening %s, terminating: %s", url, tools.error_to_str(e))
            return {}

        if url != original_url:
            logging.info("` %s", url)

            if not self.expected_url(url, limit, exclude):
                return {}

        try:
            content = page.read()
        except (socket.timeout, six.moves.http_client.HTTPException, SSLError) as e:
            logging.info("Exception while reading %s, terminating: %s", url, tools.error_to_str(e))
            return {}

        if six.PY3:
            content = content.decode()

        findings += self.check_url(url)  # 'url'
        if page:
            findings += self.check_headers(page.info())  # 'headers'
        if content:
            findings += self.check_meta(content)  # 'meta'
            findings += self.check_script(content)  # 'script'
            findings += self.check_html(content)  # 'html'

        self.follow_implies(findings)  # 'implies'
        self.remove_duplicates(findings)
        self.remove_exclusions(findings)  # 'excludes'
        self.add_categories(findings)

        return {url: findings}

    def detect_multiple(self, urls, limit=None, exclude=None, timeout=TIMEOUT):
        # remove duplicate URLs, remove empty URLs
        urls = list(set(urls) - set([None, ""]))

        results = {}
        for url in urls:
            res = self.detect(url, limit, exclude, timeout)
            results.update(res)

        return results

    @staticmethod
    def check_re(re_compiled, re_raw, text, found, det, app, show_match_only=False):
        # if re matches text, then add the app(lication) to found
        res = []
        match = re_compiled["re"].search(text)
        if match:
            ver = None

            if show_match_only:
                show_text = match.group(0)
            else:
                show_text = text

            show_text = ''.join(show_text.splitlines())

            if "version" in re_compiled:
                version_pattern = re_compiled["version"]

                # checking if version has "\\1?a:b" syntax
                # see https://github.com/AliasIO/Wappalyzer/wiki/Specification#version-syntax
                #
                # NB: Wappalyzer's implementation differs a bit:
                # https://github.com/AliasIO/Wappalyzer/blob/master/src/wappalyzer.js
                try:
                    ternary = re.match(r"^(.*)\?(.*):(.*)$", version_pattern)
                    if ternary:
                        try:
                            match.expand(ternary.group(1))
                            ver = ternary.group(2)
                        except Exception:
                            ver = ternary.group(3)
                    else:
                        ver = match.expand(version_pattern)
                except Exception as e:
                    logging.debug("Version not detected: expanding '%s' with '%s' failed: %s", show_text, re_raw,
                                  tools.error_to_str(e))
                    ver = None

                if ver:
                    ver = ver.strip()

            logging.info("  + %-7s -> %s (%s): %s =~ %s", det, app, ver, show_text, re_raw)

            res = [{'app': str(app), 'ver': ver}]
            found += res

        return res

    def check_tag(self, data, key, key_re, show_match_only=False):
        found = []
        for app in self.apps:
            if key in self.apps[app]:
                for i in range(len(self.apps[app][key_re])):
                    self.check_re(self.apps[app][key_re][i], self.apps[app][key][i], data, found, key, app,
                                  show_match_only)
        return found

    def check_url(self, url):
        return self.check_tag(data=url, key='url', key_re='url_re', show_match_only=False)

    def check_html(self, content):
        return self.check_tag(data=content, key='html', key_re='html_re', show_match_only=True)

    def check_script(self, content):
        found = []
        for tag in re_script.finditer(content):
            found.extend(self.check_tag(data=tag.group(1), key='script', key_re='script_re', show_match_only=False))
        return found

    def check_meta(self, content):
        found = []
        for tag in re_meta.finditer(content):
            for app in self.apps:
                if 'meta' in self.apps[app]:
                    for meta in self.apps[app]['meta']:
                        if tag.group(1).lower() == meta.lower():
                            self.check_re(self.apps[app]["meta_re"][meta], self.apps[app]['meta'][meta],
                                          tag.group(2), found, 'meta(%s)' % meta, app)

        return found

    def check_headers(self, headers):
        headers = dict((k.lower(), v) for k, v in headers.items())

        found = []
        for app in self.apps:
            if 'headers' in self.apps[app]:
                for entry in self.apps[app]['headers']:
                    if entry.lower() in headers:
                        self.check_re(self.apps[app]['headers_re'][entry], self.apps[app]['headers'][entry],
                                      headers[entry.lower()], found, 'headers(%s)' % entry, app)
        return found

    def implied_by(self, app_list):
        return list(set(six.moves.reduce(list.__add__,
                                         [self.apps[app]['implies'] for app in app_list if 'implies' in self.apps[app]],
                                         []))
                    - set(app_list))

    def follow_implies(self, findings):
        new = self.implied_by([f['app'] for f in findings])
        while new:
            for app in new:
                findings += [{'app': app, 'ver': None}]
                logging.info("  + %-7s -> %s", "implies", app)

            new = self.implied_by([f['app'] for f in findings])

    @staticmethod
    def remove_duplicates(findings):
        temp = copy.deepcopy(findings)

        # empty list findings
        # (keeping the existing list reference, rather than creating new list with 'findings = []' )
        findings[:] = []

        # loop over temp and insert back info findings unless it already exists
        for t in temp:
            already = False
            for f in findings:
                if t == f:
                    already = True
                elif t['app'] == f['app']:
                    # same app but different versions - now decide which one to take

                    # if f is empty or prefix of t then overwrite f with t
                    if f['ver'] is None or (t['ver'] is not None and t['ver'].find(f['ver']) == 0):
                        f['ver'] = t['ver']
                        already = True
                    # if t is empty or prefix of f, then ignore t
                    elif t['ver'] is None or f['ver'].find(t['ver']) == 0:
                        already = True

            # if t is new, then add it to final findings
            if not already:
                findings += [t]

    def excluded_by(self, app_list):
        to_exclude = list(
            set(six.moves.reduce(list.__add__,
                                 [self.apps[app]['excludes'] for app in app_list if 'excludes' in self.apps[app]], [])))
        if len(to_exclude) > 0:
            logging.info("  - excluding apps: %s", ','.join(to_exclude))
        return to_exclude

    def remove_exclusions(self, findings):
        excluded = self.excluded_by([f['app'] for f in findings])
        for app in excluded:
            for f in findings:
                if f['app'] == app:
                    findings.remove(f)

    def add_categories(self, findings):
        # some apps are in several categories => merged to a comma-separated string
        for f in findings:
            f['type'] = self.apps[f['app']]['catsStr']

    @staticmethod
    def url_match(url, regexp, default):
        if regexp:
            return re.match(regexp, url, re.IGNORECASE)
        return default

    def expected_url(self, url, limit, exclude):
        if not self.url_match(url, limit, True):
            logging.warning("x %s !~ %s", url, limit)
            return False
        if self.url_match(url, exclude, False):
            logging.warning("x %s =~ %s", url, exclude)
            return False
        return True
