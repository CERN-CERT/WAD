from __future__ import absolute_import, division, print_function, unicode_literals

import json
from wad.group import is_sub_url, group, get_dir
from wad.tests.data.data_test_wad import vinput, voutput


def test_get_dir():
    assert get_dir('/') == ('', False)
    assert get_dir('/path/bar.dir/') == ('/path/bar.dir', False)
    assert get_dir('/path//bar.dir/') == ('/path/bar.dir', False)
    assert get_dir('/path/./bar.dir/') == ('/path/bar.dir', False)
    assert get_dir('/path/./foo/../bar.dir/') == ('/path/bar.dir', False)
    assert get_dir('/path/file.ext') == ('/path', True)
    assert get_dir('/path//file.ext') == ('/path', True)
    assert get_dir('/path/./file.ext') == ('/path', True)
    assert get_dir('/path/something') == ('/path/something', False)
    assert get_dir('/path//something') == ('/path/something', False)
    assert get_dir('/site/') == ('/site', False)
    assert get_dir('/site/index.html') == ('/site', True)


def test_group():
    assert group(json.loads(vinput)) == json.loads(voutput)


def test_is_sub_url():
    assert is_sub_url('http://m.example.com/',
                      'http://m.example.com/foo')
    assert is_sub_url('http://m.example.com/foo/bar/x.y/',
                      'http://m.example.com/foo/bar/x.y/z')
    assert is_sub_url('http://m.example.com/foo/',
                      'http://m.example.com/foo/bar/x.y/z')
    assert is_sub_url('http://m.example.com/foo/#dd',
                      'http://m.example.com/foo/bar/x.y/z?fdsf')
    assert is_sub_url('http://m.example.com/foo/?adfad',
                      'http://m.example.com/foo/bar/x.y/z#sdaf')
    assert is_sub_url('http://example.com/site/',
                      'http://example.com/site/index.html')
    assert is_sub_url('http://m.example.com/foo/bar/f.txt',
                      'http://m.example.com/foo/bar/f')
    assert not is_sub_url('http://m.example.com',
                          'http://m.example.com/')
    assert not is_sub_url('http://m.example.com/foo',
                          'http://m.example.com/foo/')
    assert not is_sub_url('http://m.example.com/foo/bar/f',
                          'http://m.example.com/foo/bar/f.txt')
    assert not is_sub_url('https://m.example.com/foo/',
                          'http://m.example.com/foo/bar/x.y/z')
    assert not is_sub_url('http://example.com/foo/',
                          'https://m.example.com/foo/bar/x.y/z')
    assert not is_sub_url('http://m.example.com/foo/',
                          'http://example.com/foo/bar/x.y/z')
    assert not is_sub_url('http://x.example.com/foo/',
                          'http://m.example.com/foo/bar/x.y/z')
