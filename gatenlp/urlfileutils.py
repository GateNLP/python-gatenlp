"""
Module for functions that help reading binary and textual data from either URLs or local files.
"""

from io import TextIOWrapper
from pathlib import Path
from urllib.parse import ParseResult
from urllib.request import urlopen

import requests


def is_url(ext):
    """
    Returns a tuple (True, urlstring) if ext should be interpreted as a (HTTP(s)) URL, otherwise false, pathstring
    If ext is None, returns None, None.

    Args:
      ext: something that represents an external resource: string, url parse, pathlib path object ...

    Returns:
        a tuple (True, urlstring)  or (False,pathstring)

    """
    if ext is None:
        return None, None
    if isinstance(ext, str):
        if ext.startswith("http://") or ext.startswith("https://"):
            return True, ext
        else:
            return False, ext
    elif isinstance(ext, Path):
        return False, str(ext)
    elif isinstance(ext, ParseResult):
        return True, ext.geturl()
    else:
        raise Exception(f"Odd type: {ext}")


def get_str_from_url(url, encoding=None):
    """Read a string from the URL.

    Args:
      url: some URL
      encoding: override the encoding that would have determined automatically (Default value = None)

    Returns:
        the string
    """
    req = requests.get(url)
    if encoding is not None:
        req.encoding = encoding
    return req.text


def get_bytes_from_url(url):
    """
    Reads bytes from url.

    Args:
      url: the URL

    Returns:
        the bytes
    """
    req = requests.get(url)
    return req.content


def yield_lines_from(url_or_file, encoding="utf-8"):
    """
    Yields lines of text from either a file or an URL

    Args:
        url_or_file: either a file path or URL. If this is a string, then it is interpreted as an URL
        only if it starts with http:// or https://, otherwise it can be a parsed urllib url or a pathlib path
    """
    isurl, extstr = is_url(url_or_file)
    if isurl is None:
        return
    if isurl:
        for line in urlopen(extstr):
            line = line.decode(encoding)
            yield line
    else:
        with open(extstr, "rt", encoding=encoding) as infp:
            for line in infp:
                yield line


def stream_from(url_or_file, encoding="utf-8"):
    """
    Return an open stream from either the URL or the file, if encoding is None, in binary mode, otherwise
    in text mode with the given encoding.

    Args:
        url_or_file: URL or file
        encoding: if None, open in binary mode, otherwise in text mode with this encoding

    Returns:
        open stream or None if we cannot determine if it is an URL or file

    """
    isurl, extstr = is_url(url_or_file)
    if isurl is None:
        return
    if isurl:
        tmpfp = urlopen(extstr)
        if encoding is not None:
            return TextIOWrapper(tmpfp, encoding=encoding)
        else:
            return tmpfp
    else:
        if encoding is not None:
            return open(extstr, "rt", encoding=encoding)
        else:
            return open(extstr, "rb")