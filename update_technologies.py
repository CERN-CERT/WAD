#!/usr/bin/python3
# -*- coding: utf-8 -*-
# This script allows automatically updating the apps.json file with Wappalyzer's repo version

import sys
import string
import json
import requests
import argparse

sys.path.append("../public")

# Colors escape sequences - as in http://stackoverflow.com/questions/287871/
COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
}


def printc(string, color="HEADER"):
    """Prints the given string in the specified color."""
    print((COLORS[color] + string + COLORS["ENDC"]))


def success():
    """Prints 'Success' in green."""
    printc("Success", "OKGREEN")


class UpdateError(Exception):
    """Custom exception class for update errors."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return (
            COLORS["FAIL"]
            + 'Update failed on %s with message: "%s"' % self.msg
            + COLORS["ENDC"]
        )


BASE_URL = "https://raw.githubusercontent.com/dochne/wappalyzer"
SCHEMA_URL = f"{BASE_URL}/main/schema.json"
CATEGORIES_URL = f"{BASE_URL}/main/src/categories.json"
APPS_URL = f"{BASE_URL}/main/src/technologies"


def _download_schema(schema_file):
    """Downloads and saves the schema.json file."""
    response = requests.get(SCHEMA_URL)
    response.raise_for_status()
    schema = json.loads(response.text)
    with open(schema_file, "w") as file_path:
        json.dump(schema, file_path, indent=4)


def _download_technologies(new_file_path):
    """Downloads and updates the apps.json file with new technologies."""
    printc("\nDownloading a new version of apps.json")
    response = requests.get(CATEGORIES_URL)
    response.raise_for_status()
    cats = json.loads(response.text)
    apps = {"$schema": "../schema.json", "technologies": {}, "categories": cats}

    for letter in "_" + string.ascii_lowercase:
        try:
            response = requests.get(f"{APPS_URL}/{letter}.json")
            response.raise_for_status()
            partial_techs = json.loads(response.text)
            apps["technologies"].update(partial_techs)
        except requests.exceptions.RequestException as e:
            raise SyntaxError("Couldn't retrieve new apps.json, URLError: %s" % e)

    with open(new_file_path, "w") as new_apps_file:
        json.dump(apps, new_apps_file, indent=4)
    success()


if __name__ == "__main__":
    # Create a command-line argument parser
    parser = argparse.ArgumentParser(description="Download schema and technologies.")

    # Add an argument for the custom path (defaulting to "/etc/wad")
    parser.add_argument("--path", default="/etc/wad", help="Custom path for files")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Construct the paths using the provided custom path or the default
    apps_path = f"{args.path}/apps.json"
    schema_file = f"{args.path}/schema.json"

    _download_schema(schema_file)
    _download_technologies(apps_path)
