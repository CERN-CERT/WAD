from __future__ import absolute_import, division, print_function, unicode_literals
import six

import json
import logging
import pprint
import csv
from wad import tools


class OutputFormat(object):
    def retrieve(self, results):
        raise NotImplementedError


class JSONOutput(OutputFormat):
    """
    :return: dict dumped to string in JSON format
    """
    def retrieve(self, results):
        return json.dumps(results)


class ConsolePrettyOutput(OutputFormat):
    """
    :return: dict as string formatted with pprint
    """
    def retrieve(self, results):
        return pprint.pformat(results)


class HumanReadableOutput(OutputFormat):
    """
    :return: string formatted to be easy to read
    """
    def retrieve(self, results):
        pass


class CSVOutput(OutputFormat):
    """
    :param
    :return: string formatted as CSV
    """
    def __init__(self, filename=None):
        super(CSVOutput, self).__init__()

        self.filename = filename
        if self.filename:
            self.get_buffer = self.get_file
            self.return_handler = self.return_file
        else:
            self.get_buffer = self.get_stringio
            self.return_handler = self.return_stringio

    def retrieve(self, results):
        """
        :param results:
        :param filename:
        :return:
        """
        buf = self.get_buffer()
        fieldnames = ['URL', 'Finding', 'Version', 'Type']
        writer = csv.DictWriter(buf, fieldnames)

        writer.writeheader()
        for url, data_dicts in six.iteritems(results):
            for data in data_dicts:
                writer.writerow({'URL': url, 'Finding': data['app'], 'Version': data['ver'], 'Type': data['type']})

        return self.return_handler(buf)

    def get_stringio(self):
            return six.StringIO()

    def get_file(self):
        try:
            return open(self.filename, 'wb')
        except IOError:
            logging.error("Couldn't open %s while outputting results as csv", self.filename, tools.error_to_str(e))
            raise

    def return_stringio(self, buf):
        buf.seek(0)
        return buf.read()

    def return_file(self, buf):
        return buf
