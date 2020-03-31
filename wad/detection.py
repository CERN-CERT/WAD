from __future__ import absolute_import, division, print_function, unicode_literals
import six

from _ssl import SSLError
import copy
import logging
import socket
import re

from wad import tools
from wad.clues import Clues

# TODO: Switch to BeautifulSoup or lxml for HTML parsing purposes
re_meta = re.compile(r'<meta[^>]+>', re.IGNORECASE)
re_content = re.compile(r'content\s*=\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
re_name = re.compile(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
re_script = re.compile(r'<script[^>]+src\s*=\s*["\']([^"\']*)', re.IGNORECASE)

TIMEOUT = 3


class Detector(object):
    def __init__(self):
        self.apps, self.categories = Clues.get_clues()

    def detect(self, url, limit=None, exclude=None, timeout=TIMEOUT):
        logging.info("- %s", url)

        original_url = url

        if not self.expected_url(url, limit, exclude):
            return {}

        page = self.get_page(url=url, timeout=timeout)
        if not page:
            return {}

        url = self.get_new_url(page)

        if url != original_url:
            logging.info("` %s", url)

            if not self.expected_url(url, limit, exclude):
                return {}

        url = self.normalize_url(url)

        content = self.get_content(page, url)
        if content is None:  # Empty content is empty string, so it will pass.
            return {}

        if six.PY3:
            content = content.decode()

        findings = self.findings(url, page.info(), content)
        findings += self.additional_checks(page, url, content)

        return {url: findings}

    def findings(self, url, headers, content):
        findings = []
        findings += self.check_url(url)  # 'url'
        if headers:
            findings += self.check_headers(headers)  # 'headers'
            findings += self.check_cookies(headers)  # 'cookies'
        if content:
            findings += self.check_meta(content)  # 'meta'
            findings += self.check_script(content)  # 'script'
            findings += self.check_html(content)  # 'html'

        self.follow_implies(findings)  # 'implies'
        self.remove_duplicates(findings)
        self.remove_exclusions(findings)  # 'excludes'
        self.add_categories(findings)

        return findings

    def detect_multiple(self, urls, limit=None, exclude=None, timeout=TIMEOUT):
        # remove duplicate URLs, remove empty URLs
        urls = list(set(urls) - set([None, ""]))

        results = {}
        for url in urls:
            res = self.detect(url, limit, exclude, timeout)
            results.update(res)

        return results

    def get_content(self, page, url):
        """
        :return: Content if present, None on handled exception
        """
        try:
            content = page.read()
        except (socket.timeout, six.moves.http_client.HTTPException, SSLError) as e:
            logging.info("Exception while reading %s, terminating: %s", url, tools.error_to_str(e))
            return None
        return content

    def get_page(self, url, timeout=TIMEOUT):
        try:
            page = tools.urlopen(url, timeout=timeout)
        except six.moves.urllib.error.HTTPError as e:
            logging.warning("Error opening %s", url)
            page = e
        except six.moves.urllib.error.URLError as e:
            # a network problem? page unavailable? wrong URL?
            logging.warning("Error opening %s, terminating: %s", url, tools.error_to_str(e))
            return None
        return page

    def get_new_url(self, page):
        return page.geturl()

    def normalize_url(self, url):
        path = ''.join(six.moves.urllib.parse.urlparse(url)[2:])
        if path == '':  # ergo nothing follows top level domain
            return url + '/'
        return url

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
                        ver = ternary.group(3)
                        try:
                            if match.expand(ternary.group(1)):
                                ver = ternary.group(2)
                        except Exception:
                            pass
                    else:
                        ver = match.expand(version_pattern)
                except Exception as e:
                    logging.debug("Version not detected: expanding '%s' with '%s' failed: %s", show_text, re_raw,
                                  tools.error_to_str(e))
                    ver = None

                if ver:
                    ver = ver.strip()

            logging.info("  + %-7s -> %s (%s): %s =~ %s", det, app, ver, show_text, re_raw)

            res = [{'app': str(app), 'ver': ver or None}]
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
            meta_tag = tag.group(0)
            name_matches = re_name.findall(meta_tag)
            content_matches = re_content.findall(meta_tag)
            if not name_matches or not content_matches:
                continue

            name = name_matches[0]
            content = content_matches[0]
            for app in self.apps:
                if 'meta' in self.apps[app]:
                    for meta in self.apps[app]['meta']:
                        if name.lower() == meta.lower():
                            self.check_re(self.apps[app]["meta_re"][meta], self.apps[app]['meta'][meta],
                                          content, found, 'meta(%s)' % meta, app)

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

    def check_cookies(self, headers):
        cookies = dict()
        for cookie in headers.get('Set-Cookie', '').split(';'):
            if '=' in cookie:
                sep = cookie.index('=')
                cookie_name = cookie[:sep].strip()
                cookie_val = cookie[sep+1:].strip()
                cookies[cookie_name] = cookie_val

        if not cookies:
            return []

        found = []
        for app in self.apps:
            if 'cookies' in self.apps[app]:
                for entry in self.apps[app]['cookies']:
                    if entry in cookies:
                        self.check_re(self.apps[app]['cookies_re'][entry], self.apps[app]['cookies'][entry],
                                      cookies[entry], found, 'cookies(%s)' % entry, app)
        return found

    def implied_by(self, app_list):
        all_implied = [implied for app in app_list
                       if 'implies' in self.apps.get(app, {})
                       for implied in self.apps[app]['implies']]
        implied_new = set(all_implied) - set(app_list)
        return implied_new

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

    def additional_checks(self, page, url, content):
        """
        It can be overrided in order to perform more checks over the website
        :param page: page retrieved with urllib2
        :param url: page url
        :param content: decoded content
        :return: list of findings
        """
        return []
