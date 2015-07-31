# Clues taken from Wappalyzer
#
# clues:        https://github.com/AliasIO/Wappalyzer/blob/master/src/apps.json
# more info:    https://github.com/AliasIO/Wappalyzer/blob/master/README.md
# detection:    https://github.com/AliasIO/Wappalyzer/blob/master/src/wappalyzer.js
# JavaScript RegExp object: http://www.w3schools.com/jsref/jsref_obj_regexp.asp
from __future__ import absolute_import, division, print_function, unicode_literals
import six

import os
import logging
import re
import json

from wad import tools

CLUES_FILE = os.path.join(os.path.dirname(__file__), 'etc/apps.json')


class _Clues(object):
    def __init__(self):
        self.apps = None
        self.categories = None

    def get_clues(self, filename=CLUES_FILE):
        if self.apps and self.categories:
            return self.apps, self.categories

        self.load_clues(filename)
        self.compile_clues()
        return self.apps, self.categories

    @staticmethod
    def read_clues_from_file(filename):
        logging.info("Reading clues file %s", filename)
        try:
            json_data = open(filename)
        except IOError as e:
            logging.error("Error while opening clues file, terminating: %s", tools.error_to_str(e))
            raise

        try:
            clues = json.load(json_data, encoding='utf-8')
        except ValueError as e:
            logging.error("Error while reading JSON file, terminating: %s", tools.error_to_str(e))
            raise

        json_data.close()
        categories = clues['categories']
        apps = clues['apps']
        return apps, categories

    @staticmethod
    def merge_dictionaries(dict1, dict2, desc):
        for key in dict2:
            if key in dict1:
                logging.warning("%s '%s' in both clues files", desc, key)
            dict1[key] = dict2[key]

    def string_to_array(self, tag):
        for app in self.apps:
            if tag in self.apps[app]:
                if type(self.apps[app][tag]) is six.text_type:
                    self.apps[app][tag] = [self.apps[app][tag]]

    def ignore_attributes(self, tag):
        # ignore all attributes (such as "confidence") specified after \;
        for app in self.apps:
            if tag in self.apps[app]:
                new_list = []
                for item in self.apps[app][tag]:
                    values = item.split("\;")
                    new_list += [values[0]]
                self.apps[app][tag] = new_list

    def add_categories_str(self):
        for app in self.apps:
            self.apps[app]['catsStr'] = six.moves.reduce(lambda a, b: "%s,%s" % (a, b),
                                                         [str(self.categories[str(x)]) for x in self.apps[app]['cats']])

    def load_clues(self, filename):
        self.apps, self.categories = self.read_clues_from_file(filename)

        additional_clues = filename + ".other"
        if os.path.isfile(additional_clues):
            apps2, categories2 = self.read_clues_from_file(additional_clues)
            # merge dictionaries with apps and categories; warn about repeated ones
            self.merge_dictionaries(self.apps, apps2, "App")
            self.merge_dictionaries(self.categories, categories2, "Category")

        # some clues are strings while others are array of strings - make them all arrays
        for field in ['url', 'html', 'env', 'script', 'implies', 'excludes']:
            self.string_to_array(field)

        # ignoring confidence in implies and excludes
        self.ignore_attributes('implies')
        self.ignore_attributes('excludes')

        # add categories string field
        self.add_categories_str()

    @staticmethod
    def compile_clue(regexp_extended):
        values = regexp_extended.split("\;")
        regex_dict = {"re": re.compile(values[0], flags=re.IGNORECASE)}
        for extra_field in values[1:]:
            try:
                (k, v) = extra_field.split(':', 1)
                regex_dict[k] = v
            except ValueError:
                regex_dict[extra_field] = None

        return regex_dict

    def compile_clues(self):
        # compiling regular expressions
        for app in self.apps:
            regexps = {}
            for key in self.apps[app]:
                if key in ['script', 'html', 'url']:
                    regexps[key + "_re"] = list(six.moves.map(self.compile_clue, self.apps[app][key]))
                if key in ['meta', 'headers']:
                    regexps[key + "_re"] = {}
                    for entry in self.apps[app][key]:
                        regexps[key + "_re"][entry] = self.compile_clue(self.apps[app][key][entry])
            self.apps[app].update(regexps)


Clues = _Clues()  # For use as singleton
