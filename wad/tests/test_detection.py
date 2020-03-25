from __future__ import absolute_import, division, print_function, unicode_literals
import six

import copy
import unittest
import mock
import operator

from wad.detection import Detector, TIMEOUT
from wad.tests.data.data_test_wad import cern_ch_test_data


class TestDetector(unittest.TestCase):
    def setUp(self):
        self.detector = Detector()
        self.apps = self.detector.apps
        self.categories = self.detector.categories

    def mock_detector_run(self, url='', content='', headers=None):
        with mock.patch('wad.detection.tools') as mockObj:
            page = mock.MagicMock()
            page.geturl.return_value = url
            if six.PY3:
                page.read.return_value = bytes(content, encoding='utf-8')
            else:
                page.read.return_value = content
            page.info.return_value = headers or dict()
            mockObj.urlopen = mock.Mock(return_value=page)
            results = self.detector.detect('http://abc.xyz')
        return results

    def test_check_re(self):
        # checking version patterns:
        #
        #   "headers": { "Server": "IIS(?:/([\\d.]+))?\\;version:\\1" },
        assert (self.detector.check_re(
            self.apps['IIS']['headers_re']['Server'],
            self.apps['IIS']['headers']['Server'],
            'Microsoft-IIS/7.5',
            [], None, 'IIS') == [{'app': 'IIS', 'ver': '7.5'}])

        # (?:maps\\.google\\.com/maps\\?file=api(?:&v=([\\d.]+))?|
        # maps\\.google\\.com/maps/api/staticmap)\\;version:API v\\1
        assert (self.detector.check_re(
            self.apps['Google Maps']['script_re'][0],
            self.apps['Google Maps']['script'][0],
            'abc <script src="maps.google.com/maps?file=api&v=123"> def',
            [], None, 'Google Maps') == [{'app': 'Google Maps', 'ver': 'API v123'}])

        # "script": [ "js/mage", "skin/frontend/(?:default|(enterprise))\\;version:\\1?Enterprise:Community" ],
        assert (self.detector.check_re(
            self.apps['Magento']['script_re'][1],
            self.apps['Magento']['script'][1],
            'abc <script src="skin/frontend/whatever"> def',
            [], None, 'Magento') == [])

        assert (self.detector.check_re(
            self.apps['Magento']['script_re'][1],
            self.apps['Magento']['script'][1],
            'abc <script src="skin/frontend/default"> def',
            [], None, 'Magento') == [{'app': 'Magento', 'ver': 'Community'}])

        assert (self.detector.check_re(
            self.apps['Magento']['script_re'][1],
            self.apps['Magento']['script'][1],
            'abc <script src="skin/frontend/enterprise"> def',
            [], None, 'Magento') == [{'app': 'Magento', 'ver': 'Enterprise'}])

    def test_check_url(self):
        assert self.detector.check_url("http://whatever.blogspot.com") == [{'app': 'Blogger', 'ver': None}]
        assert self.detector.check_url("https://whatever-else3414.de/script.php") == [{'app': 'PHP', 'ver': None}]

    def test_check_html(self):
        content = '<html><div id="gsNavBar" class="gcBorder1">whatever'
        assert self.detector.check_html(content) == [{'app': 'Gallery', 'ver': None}]

    def test_check_meta(self):
        assert (self.detector.check_meta('<html>    s<meta name="generator" content="Percussion">sssss    whatever') ==
                [{'app': 'Percussion', 'ver': None}])
        assert (self.detector.check_meta(" dcsaasd f<meta   name    = 'cargo_title' dd  content  =   'Pdafadfda'  >") ==
                [{'app': 'Cargo', 'ver': None}])
        assert (self.detector.check_meta(" dcsaasd f<mfffffffeta     name='cargo_title' dd  content='Pdafadfda'  >") ==
                [])
        assert self.detector.check_meta(" dcsaasd f<meta     name='cargo_title' >") == []

    def test_check_script(self):
        assert (self.detector.check_script('<html>    s<script  sda f     src    =  "jquery1.7.js">') ==
                [{'app': 'jQuery', 'ver': None}])
        assert self.detector.check_script(" dcsaasd f<script     src='' >") == []

    def test_check_headers(self):
        headers = [('Host', 'abc.com'), ('Server', 'Linux Ubuntu 12.10')]
        headers_mock = mock.Mock()
        headers_mock.items.return_value = headers

        assert (self.detector.check_headers(headers_mock) ==
                [{'app': 'Ubuntu', 'ver': None}])

    def test_check_cookies(self):
        headers = {'Set-Cookie': 'x=1; xid=%s; y=2' % ('a'*32)}

        assert (self.detector.check_cookies(headers) ==
                [{'app': 'X-Cart', 'ver': None}])

    def test_implied_by(self):
        # ASP implies WS and IIS and IIS implies WS;
        # but we already know about IIS, so the only new implied app is WS
        assert self.detector.implied_by(['Microsoft ASP.NET', 'IIS']) == {'Windows Server'}

    def test_follow_implies(self):
        # empty findings
        findings = []
        self.detector.follow_implies(findings)
        assert findings == []

        # no implies
        findings = [{'app': 'reCAPTCHA', 'ver': None}]
        self.detector.follow_implies(findings)
        assert findings == [{'app': 'reCAPTCHA', 'ver': None}]

        # Django CMS implies Django, and Django implies Python - let's see if this chain is followed
        findings = [{'app': 'Django CMS', 'ver': None}]
        self.detector.follow_implies(findings)
        assert (findings ==
                [{'app': 'Django CMS', 'ver': None},
                 {'app': 'Django', 'ver': None},
                 {'app': 'Python', 'ver': None}])

    def test_remove_duplicates(self):
        with_duplicates = [
            {'app': 'A', 'ver': None}, {'app': 'B', 'ver': "1.5"},
            {'app': 'C', 'ver': None}, {'app': 'D', 'ver': "7.0"},
            {'app': 'E', 'ver': "1"}, {'app': 'F', 'ver': "2.2"},
            {'app': 'A', 'ver': None}, {'app': 'B', 'ver': "1.5"},
            {'app': 'C', 'ver': "be"}, {'app': 'D', 'ver': "222"},
            {'app': 'A', 'ver': None}, {'app': 'B', 'ver': "1.5"},
            {'app': 'E', 'ver': None}, {'app': 'E', 'ver': "1.3"},
            {'app': 'F', 'ver': "2"}, {'app': 'F', 'ver': None},
        ]

        without_duplicates = [
            {'app': 'A', 'ver': None}, {'app': 'B', 'ver': "1.5"},
            {'app': 'C', 'ver': "be"}, {'app': 'D', 'ver': "7.0"},
            {'app': 'E', 'ver': "1.3"},
            {'app': 'F', 'ver': "2.2"}, {'app': 'D', 'ver': "222"},
        ]

        Detector().remove_duplicates(with_duplicates)
        assert with_duplicates == without_duplicates

    def test_excluded_by(self):
        # both 'Neos Flow' and 'Neos CMS' exclude 'TYPO3 CMS'
        assert self.detector.excluded_by(['Neos Flow', 'Neos CMS']) == ['TYPO3 CMS']
        # 'JBoss Web' excludes 'Apache Tomcat'; 'Mambo' excludes 'Joomla'
        assert set(self.detector.excluded_by(['JBoss Web', 'Jetty', 'Mambo'])) == set(['Joomla', 'Apache Tomcat'])
        # 'IIS' doesn't exclude anything
        assert self.detector.excluded_by(['IIS']) == []

    def test_remove_exclusions(self):
        # empty findings
        findings = []
        self.detector.remove_exclusions(findings)
        assert findings == []

        # no implies
        findings = [{'app': 'reCAPTCHA', 'ver': None}]
        self.detector.remove_exclusions(findings)
        assert findings == [{'app': 'reCAPTCHA', 'ver': None}]

        # real exclusions
        findings = [{'app': 'JBoss Web', 'ver': None},
                    {'app': 'Apache Tomcat', 'ver': None},
                    {'app': 'IIS', 'ver': None},
                    {'app': 'TYPO3 CMS', 'ver': None},
                    {'app': 'Neos Flow', 'ver': None}]
        self.detector.remove_exclusions(findings)
        assert (findings ==
                [{'app': 'JBoss Web', 'ver': None},
                 {'app': 'IIS', 'ver': None},
                 {'app': 'Neos Flow', 'ver': None}])

    def test_add_categories(self):
        findings = [
            {'app': 'Django CMS', 'ver': None},
            {'app': 'Django', 'ver': None},
            {'app': 'Python', 'ver': '2.7'},
            {'app': 'Dynamicweb', 'ver': 'beta'}]
        original = copy.deepcopy(findings)
        original[0]["type"] = "CMS"
        original[1]["type"] = "Web Application Frameworks"
        original[2]["type"] = "Programming Languages"
        original[3]["type"] = "CMS,Ecommerce,Analytics"

        self.detector.add_categories(findings)
        assert original == findings

    def test_url_match(self):
        assert self.detector.url_match(url='', regexp=None, default='test') == 'test'
        assert self.detector.url_match(url='example.com', regexp='exampl', default='test') is not None
        assert self.detector.url_match(url='example.com', regexp='ampl', default='test') is None

    def test_expected_url(self):
        url = "http://site.abc.com/dir/sub/script.php"
        assert self.detector.expected_url(url, None, None)
        assert self.detector.expected_url(url, 'http://.*abc.com/', None)
        assert not self.detector.expected_url(url, 'http://abc.com/', None)
        assert self.detector.expected_url(url, 'http://.*abc.com/', "php")
        assert not self.detector.expected_url(url, 'http://.*abc.com/', ".*php")
        assert self.detector.expected_url(url, None, ".*\\.asp")
        assert not self.detector.expected_url(url, None, ".*\\.php")

    def test_detect(self):
        expected = {
            'http://home.web.cern.ch/': [
                {'app': 'Apache', 'type': 'Web Servers', 'ver': None},
                {'app': 'Drupal', 'type': 'CMS', 'ver': '7'},
                {'app': 'Lightbox', 'type': 'JavaScript Libraries', 'ver': None},
                {'app': 'jQuery', 'type': 'JavaScript Libraries', 'ver': None},
                {'app': 'Google Font API', 'type': 'Font Scripts', 'ver': None},
                {'app': 'PHP', 'type': 'Programming Languages', 'ver': None}
            ]
        }

        results = self.mock_detector_run(url=cern_ch_test_data['geturl'], content=cern_ch_test_data['content'],
                                         headers=cern_ch_test_data['headers'])
        assert list(six.iterkeys(results)) == list(six.iterkeys(expected))
        assert (sorted(next(six.itervalues(results)), key=operator.itemgetter('app')) ==
                sorted(next(six.itervalues(expected)), key=operator.itemgetter('app')))

    def test_detect_multiple(self):
        urls_list = ["http://cern.ch", None, "", "http://cern.ch", "example.com"]
        with mock.patch('wad.detection.Detector.detect') as mockObj:
            mockObj.side_effect = [{'test1': 1}, {'test2': 2}]
            assert self.detector.detect_multiple(urls_list) == {'test1': 1, 'test2': 2}
            assert (('example.com', None, None, TIMEOUT),) in mockObj.call_args_list
            assert (('http://cern.ch', None, None, TIMEOUT),) in mockObj.call_args_list

    def test_normalize_url(self):
        assert self.detector.normalize_url('http://abc.pl') == 'http://abc.pl/'
        assert self.detector.normalize_url('http://abc.pl/') == 'http://abc.pl/'
        assert self.detector.normalize_url('http://abc.pl/def') == 'http://abc.pl/def'

    def test_regression_meta_attributes_order(self):
        # This bug was caused by hardcoded attributes order in re_meta pattern.
        # Example app that was affected was GitLab CI.
        content1 = "<meta content='GitLab Continuous Integration' name='description'>"
        content2 = "<meta name='description' content='GitLab Continuous Integration'>"

        results1 = self.detector.check_meta(content1)
        results2 = self.detector.check_meta(content2)

        expected = [{'app': 'GitLab CI', 'ver': None}]

        assert results1 == results2 == expected

    def test_regression_empty_content_should_run_checks(self):
        # This bug was introduced while abstracting some methods in detect method of Detector
        # Shortly, if the content was empty, code didn't run further (while it should, there might be something in
        # headers etc.)
        expected = {
            'http://home.web.cern.ch/': [
                {'app': 'Apache', 'type': 'Web Servers', 'ver': None},
                {'app': 'Drupal', 'type': 'CMS', 'ver': '7'},
                {'app': 'PHP', 'type': 'Programming Languages', 'ver': None}
            ]
        }
        results = self.mock_detector_run(url=cern_ch_test_data['geturl'], content='',
                                         headers=cern_ch_test_data['headers'])
        assert list(six.iterkeys(results)) == list(six.iterkeys(expected))
        assert (sorted(next(six.itervalues(results)), key=operator.itemgetter('app')) ==
                sorted(next(six.itervalues(expected)), key=operator.itemgetter('app')))

    def test_regression_urls_not_normalized(self):
        # This bug caused .pl top level domain to be recognized as Perl file.
        # It is due to the fact, that Wappalyzer receives normalized URI from browser ("http://abc.xyz/")
        # even if you open "http://abc.xyz", while we didn't normalize the URL.
        results = self.mock_detector_run(url='http://abc.pl')
        assert results == {'http://abc.pl/': []}
