"""
Module for functions that help reading binary and textual data from either URLs or local files.
"""

from typing import Optional, Union
from io import TextIOWrapper
from pathlib import Path
import asyncio
from urllib.parse import ParseResult
from urllib.request import urlopen
have_pyodide = False
try:
    import requests
except Exception as ex:
    # maybe importing requests failed because we are running in a browser using pyodide?
    try:
        import pyodide
        from pyodide import open_url
        have_pyodide = True
    except:
        # nope, re-raise the original exception
        raise ex

def is_url(ext: Union[str, Path, ParseResult, None]):
    """
    Returns a tuple (True, urlstring) if ext should be interpreted as a (HTTP(s)) URL, otherwise false, pathstring
    If ext is None, returns None, None. If ext is a string, it only gets interpreted as a URL if it starts with
    http:// or https://, and if it starts with file:// the remaining path is used (the latter probably only works on
    non-Windows systems). Otherwise the string is interpreted as a file path.
    If ext is a ParseResult it is always interpreted as a URL, if it is a Path object it is always interpreted
    as a path.

    Args:
        ext: something that represents an external resource: a string, a ParseResult i.e.
            the result of urllib.parse.urlparse(..), a Path i.e. the result of  Path(somepathstring).

    Returns:
        a tuple (True, urlstring)  or (False,pathstring), or None, None if ext is None

    """
    if ext is None:
        return None, None
    if isinstance(ext, str):
        if ext.startswith("http://") or ext.startswith("https://"):
            return True, ext
        else:
            # for now, if we have ext starting with file:// we just remove that part and assume the
            # rest is supposed to be a proper file path
            if ext.startswith("file://"):
                ext = ext[7:]
            return False, ext
    elif isinstance(ext, Path):
        return False, str(ext)
    elif isinstance(ext, ParseResult):
        return True, ext.geturl()
    else:
        raise Exception(f"Odd type: {ext}")


def get_str_from_url(url: Union[str, ParseResult], encoding=None):  # pragma: no cover
    """
    Read a string from the URL.

    Args:
      url: some URL
      encoding: override the encoding that would have determined automatically (Default value = None)

    Returns:
        the string
    """
    if isinstance(url, ParseResult):
        url = url.geturl()
    if have_pyodide:
        with open_url(url) as infp:
            text = infp.read()
        return text
    req = requests.get(url, allow_redirects=True)
    if encoding is not None:
        req.encoding = encoding
    return req.text


async def get_bytes_from_url_pyodide(url):
    """
    Fetches bytes from the URL using GET.

    Args:
        url: url to use

    Returns:
        bytes
    """
    response = await pyodide.http.pyfetch(url, method="GET")
    bytes = await response.bytes()
    return bytes


def get_bytes_from_url(url):  # pragma: no cover
    """
    Reads bytes from url.

    Args:
      url: the URL

    Returns:
        the bytes
    """
    if have_pyodide:
        return asyncio.run(get_bytes_from_url_pyodide(url))
    req = requests.get(url, allow_redirects=True)
    return req.content


def yield_lines_from(url_or_file: Union[str, Path, ParseResult], encoding: str = "utf-8"):  # pragma: no cover
    """
    Yields lines of text from either a file or an URL

    Args:
        url_or_file: either a file path or URL. If this is a string, then it is interpreted as an URL
            only if it starts with http:// or https://, otherwise it can be a parsed urllib url
            or a pathlib path
        encoding: the encoding to use
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


def stream_from(url_or_file: Union[str, Path, ParseResult], encoding: str = "utf-8"):  # pragma: no cover
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
