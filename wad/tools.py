# Module tools
#
# Author: Sebastian Lopienski <Sebastian.Lopienski@cern.ch>

import six

from hashlib import md5
import logging
import sys
import ssl

from six.moves import http_client
import logging
import requests
from collections import Counter


def count(d, e):
    if isinstance(e, list):
        counter = Counter(e)
        d.update(counter)
    else:
        if e in d:
            d[e] += 1
        else:
            d[e] = 1


def hash_id(x):
    return md5(("%s" % x).encode("utf-8")).hexdigest()[:8]


def urlopen(url, timeout):
    # http_client.HTTPConnection.debuglevel = 1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("requests.packages.urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True
    # six.moves.urllib.request.HTTPHandler(debuglevel=1)

    # headers = {'User-Agent': 'Mozilla/5.0 Firefox/33.0'}
    page = requests.get(url, verify=True, timeout=60)
    # req = six.moves.urllib.request.Request(url, None, headers)
    # if sys.version_info >= (2, 7, 9):
    #    page = six.moves.urllib.request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context())
    # else:
    #    page = six.moves.urllib.request.urlopen(req, timeout=timeout)
    return page


def error_to_str(e):
    return str(e).replace("\n", "\\n")


def add_log_options(parser):
    parser.add_argument(
        "-q", "--quiet", action="store_true", dest="quiet", default=False, help="be quiet"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="be verbose",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="be more verbose",
    )

    parser.add_argument(
        "--log",
        action="store",
        dest="log_file",
        metavar="FILE",
        default=None,
        help="log to a file instead of standard output",
    )


def use_log_options(options):
    log_format = (
        "%(asctime)s ("
        + hash_id(options.__str__())
        + "):%(module)s:%(levelname)s %(message)s"
    )

    date_format = "%Y/%m/%d-%H:%M:%S"
    log_level = logging.WARNING

    if options.verbose:
        log_level = logging.INFO
    if options.debug:
        log_level = logging.DEBUG
    if options.quiet:
        log_level = logging.ERROR

    if options.log_file:
        logging.basicConfig(
            filename=options.log_file,
            level=log_level,
            format=log_format,
            datefmt=date_format,
        )
    else:
        logging.basicConfig(
            stream=sys.stdout, level=log_level, format=log_format, datefmt=date_format
        )
