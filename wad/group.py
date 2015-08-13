from __future__ import absolute_import, division, print_function, unicode_literals
import six

import logging
import os.path


def get_dir(url_path):
    if url_path == "" or url_path == "/":
        return "", False

    normfilename = os.path.normpath(url_path)
    # /path/sub.dir/ -> /path/sub.dir
    if url_path.endswith("/"):
        return normfilename, False

    # /path/file.ext -> /path
    e = normfilename.split("/")
    if e[-1].find('.') >= 0:
        return '/'.join(e[:-1]), True

    # /path/something -> /path/something
    return normfilename, False


def subpath_starts_with(s, subs, subpath_had_extension=False):
    if subpath_had_extension:
        return s.find(subs) == 0
    return s.find(subs) == 0 and s != subs


def is_sub_url(url, suburl):
    if url == suburl:
        return False

    parsed_url = six.moves.urllib.parse.urlparse(url)
    parsed_suburl = six.moves.urllib.parse.urlparse(suburl)

    if parsed_url[:2] != parsed_suburl[:2]:
        return False

    path, __ = get_dir(parsed_url[2])
    subpath, subpath_had_extension = get_dir(parsed_suburl[2])

    return subpath_starts_with(subpath, path, subpath_had_extension)


def group(results):
    logging.info("Grouping results")
    # for each pair of URLs, if one is a suburl of the other, then remove from
    # the latter url any technologies detected also for the former
    for url in results:
        for url2 in results:
            if is_sub_url(url, url2):
                logging.debug("--> %s\n`-> %s\n", url, url2)
                for finding in results[url]:
                    if finding in results[url2]:
                        results[url2].remove(finding)
                        logging.debug("Removing %s from %s, as %s also has it", finding, url2, url)

    # ... and then remove any urls without any findings
    for url in results.keys():
        if not results[url]:
            results.pop(url)

    return results
