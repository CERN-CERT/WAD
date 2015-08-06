import unittest
import six
from wad.output import JSONOutput, ConsolePrettyOutput, CSVOutput


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
        JSONOutput().retrieve(results=self.input)
        ConsolePrettyOutput().retrieve(results=self.input)

    def test_human_readable_output(self):
        pass

    def test_csv_output(self):
        expected_lines = [
            'URL,Finding,Version,Type',
            'http://example2.com/,Apache,ABC,web-servers',
            'https://example1.com/,Python,2.7.6,programming-languages',
            'https://example1.com/,jQuery,,javascript-frameworks'
        ]
        results = six.StringIO(CSVOutput().retrieve(results=self.input)).readlines()
        results = [line.strip() for line in results]
        self.assertSetEqual(set(expected_lines), set(results))
