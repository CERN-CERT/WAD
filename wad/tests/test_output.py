from __future__ import absolute_import, division, print_function, unicode_literals
import six

import unittest
from wad.output import JSONOutput, ConsolePrettyOutput, CSVOutput, HumanReadableOutput


class TestOutputs(unittest.TestCase):
    def setUp(self):
        self.input = {
            "https://example1.com/": [
                {"type": "programming-languages", "app": "Python", "ver": '2.7.6'},
                {"type": "javascript-frameworks", "app": "jQuery", "ver": None},
            ],
            "http://example2.com/": [{"type": "web-servers", "app": "Apache", "ver": 'ABC'}]
        }

    def test_basic_outputs(self):
        """
        We don't need to check exact output, just successful invocation, since functions only use native python libs
        """
        assert JSONOutput().retrieve(results=self.input) != ''
        assert JSONOutput().retrieve(results=self.input, indent=None) != ''
        assert ConsolePrettyOutput().retrieve(results=self.input) != ''

    def test_human_readable_output(self):
        expected_output = [
            'Web application detection results for website https://example1.com/, found applications:',
            'Python (programming-languages), version: 2.7.6',
            'jQuery (javascript-frameworks)',
            'Web application detection results for website http://example2.com/, found applications:',
            'Apache (web-servers), version: ABC',
        ]
        output = HumanReadableOutput().retrieve(self.input)
        results = [line.strip() for line in six.StringIO(output).readlines()]
        # Remove empty lines after stripping
        results = [line for line in results if line != '']
        assert set(expected_output) == set(results)

    def test_csv_output(self):
        expected_lines = [
            'URL,Finding,Version,Type',
            'http://example2.com/,Apache,ABC,web-servers',
            'https://example1.com/,Python,2.7.6,programming-languages',
            'https://example1.com/,jQuery,,javascript-frameworks'
        ]
        output = CSVOutput().retrieve(results=self.input)
        results = [line.strip() for line in six.StringIO(output).readlines()]
        assert set(expected_lines) == set(results)
