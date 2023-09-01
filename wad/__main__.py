# -*- coding: utf-8 -*-
#
# Author: Sebastian.Lopienski@cern.ch
#

import logging
import argparse
from wad import tools
from wad.clues import Clues
from wad.detection import TIMEOUT, Detector
from wad.group import group
from wad.output import JSONOutput, CSVOutput, HumanReadableOutput

output_format_map = {
    "csv": CSVOutput,
    "json": JSONOutput,
    "txt": HumanReadableOutput,
}


def main(timeout=TIMEOUT):
    desc = """WAD -
This component analyzes given URL(s) and detects technologies, libraries,
frameworks, etc. used by this application, from the OS and web server level,
to the programming platform and frameworks, and server- and client-side
applications, tools, and libraries. For example: OS=Linux, webserver=Apache,
platform=PHP, CMS=Drupal, analytics=Google Analytics, javascript-lib=jQuery
etc."""

    parser = argparse.ArgumentParser(
        description=desc,
        usage="%(prog)s -u <URLs|@URLfile>\nHelp: %(prog)s -h",
        version="%(prog)s 1.0",
    )

    parser.add_argument(
        "-u",
        "--url",
        dest="urls",
        metavar="URLS|@FILE",
        help="list of URLs (comma-separated), or a file with a list of URLs (one per line)",
    )

    parser.add_argument(
        "-l",
        "--limit",
        dest="limit",
        metavar="URLMASK",
        help="in case of redirections, only include pages with URLs matching this mask - "
        "e.g. 'https?://[^/]*\\.abc\\.com/'",
    )

    parser.add_argument(
        "-x",
        "--exclude",
        dest="exclude",
        metavar="URLMASK",
        help="in case of redirections, exclude pages with URL matching this mask - "
        "e.g. 'https?://[^/]*/(login|logout)'",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        metavar="FILE",
        help="output file for detection results (default: STDOUT)",
    )

    parser.add_argument(
        "-c",
        "--clues",
        dest="clues_file",
        metavar="FILE",
        default=None,
        help="clues for detecting web applications and technologies",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        action="store",
        dest="TIMEOUT",
        default=timeout,
        help="set timeout (in seconds) for accessing a single URL",
    )

    parser.add_argument(
        "-f",
        "--format",
        action="store",
        dest="format",
        default="json",
        help="output format, allowed values: csv, txt, json (default)",
    )

    parser.add_argument(
        "-g",
        "--group",
        action="store_true",
        dest="group",
        default=False,
        help="group results (i.e. technologies found on subpages of other scanned URL "
        "aren't listed)",
    )

    tools.add_log_options(parser)

    args = parser.parse_args()

    tools.use_log_options(args)

    if not args.urls:
        parser.error("Argument -u missing")
        return

    timeout = int(args.TIMEOUT)

    if args.urls[0] == "@":
        try:
            with open(args.urls[1:]) as f:
                urls = f.readlines()
        except Exception as e:
            # an I/O exception?
            logging.error(
                "Error reading URL file %s, terminating: %s",
                args.urls[1:],
                tools.error_to_str(e),
            )
            return
    else:
        urls = [x.strip() for x in args.urls.split(",") if x.strip() != ""]

    if args.format not in list(output_format_map.keys()):
        parser.error("Invalid format specified")
        return

    Clues.get_clues(args.clues_file)

    results = Detector().detect_multiple(
        urls, limit=args.limit, exclude=args.exclude, timeout=timeout
    )

    if args.group:
        results = group(results)

    output = output_format_map[args.format]().retrieve(results=results)

    if args.output_file:
        try:
            with open(args.output_file, "w") as f:
                f.write(output)
                logging.debug("Results written to file %s", args.output_file)
        except Exception as e:
            # an I/O exception?
            logging.error(
                "Error writing results to file %s, terminating: %s",
                args.output_file,
                tools.error_to_str(e),
            )
            return

    print(output)


if __name__ == "__main__":
    main()
