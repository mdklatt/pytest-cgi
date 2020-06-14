""" Implementation of the `cgi` test fixture.

This will capture the output of an external script executed via a CGI request,
i.e. GET or POST.

"""
from io import BytesIO
from pathlib import Path
from shlex import split
from subprocess import PIPE
from subprocess import run
from typing import Union
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen

import pytest


__all__ = "cgi_local", "cgi_remote"


class LocalClient(object):
    """ Invoke a local CGI script via the command line.

    :var self.status: HTTP status code
    :var self.header: HTTP header values
    :var self.content: HTTP content
    :var self.stderr: STDERR output from local script
    """
    def __init__(self):
        """ Initialize this object.

        """
        self.headers = {}
        self.content = None
        self.status = None
        self.stderr = None
        return

    def get(self, script: Union[str, Path], query: dict):
        """ Execute a GET request.

        :param script: script path
        :param query: mapping of query parameters
        """
        env = {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": urlencode(query, doseq=True),
        }
        self._call(script, env)
        return

    def post(self, script: Union[str, Path], data, mime="text/plain"):
        """ Execute a POST request.

        :param script: script path
        :param data: text data or mapping of query parameters
        :param mime: data MIME type
        """
        if isinstance(data, dict):
            data = urlencode(data, doseq=True).encode()
            mime = "application/x-www-form-urlencoded"
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": str(len(data)),
            "CONTENT_TYPE": mime,
        }
        self._call(script, env, data)
        return

    def _call(self, path: Union[Path, str], env: dict, data=None):
        """ Call a local CGI script via the command line.

        :param path: script path
        :param env: mapping of environment variables
        :param data: input data
        """
        args = split(str(path))
        process = run(args, input=data, stdout=PIPE, stderr=PIPE, env=env)
        self._response(process.stdout)
        self.stderr = process.stderr.decode()
        return

    def _response(self, response: bytes):
        """ Parse the response returned by the application.

        :param response: HTTP response
        """
        headers = []
        with BytesIO(response) as stream:
            for line in stream:
                # Get header lines.
                line = line.decode().strip()
                if not line:  # found the end of the header
                    break
                headers.append(line)
            self.content = stream.read()
        try:
            if headers[0].lstrip().lower().startswith("http"):
                # Be lenient about accepting non-standard headers.
                # <https://tools.ietf.org/html/rfc7230>
                self.status = int(headers[0].split()[1])  # integer status
                headers.pop(0)
        except IndexError:  # empty headers
            pass
        for line in headers:
            # Convert headers to a dict.
            key, value = (item.strip() for item in line.split(":", 1))
            key = key.lower()  # field names are not case sensitive
            try:
                self.headers[key].append(value)
            except KeyError:
                # First instance of this key.
                self.headers[key] = value
            except AttributeError:
                # Second instance of this key, start a list.
                self.headers[key] = [self.headers[key], value]
        return


class RemoteClient(object):
    """ Invoke a remote CGI script via a URL.

    :var self.status: HTTP status code
    :var self.header: HTTP header values
    :var self.content: HTTP content
    """
    def __init__(self):
        """ Initialize this object.

        """
        self.headers = {}
        self.content = None
        self.status = None
        return

    def get(self, script: str, query: dict):
        """ Execute a GET request.

        :param script: script URL
        :param query: dict-like object of query parameters
        """
        url = "?".join((script, urlencode(query, doseq=True)))
        self._call(url, "GET")
        return

    def post(self, script: str, data: Union[bytes, dict], mime="text/plain"):
        """ Execute a POST request.

        :param script: script URL
        :param data: binary data or mapping of query parameters
        :param mime: data MIME type
        """
        if isinstance(data, dict):
            data = urlencode(data, doseq=True).encode()
            mime = "application/x-www-form-urlencoded"
        headers = {
            "Content-Type": mime,
            "Content-Length": len(data)
        }
        self._call(script, "POST", data, headers)
        return

    def _call(self, url: str, method: str, data=None, headers=None):
        """ Call a CGI script via URL.

        :param url: script URL
        :param method: request method (GET or POST)
        :param data: binary data
        :param headers: dict-like mapping of HTTP headers
        """
        request = Request(url, data, headers or {}, method=method)
        with urlopen(request) as response:
            self.content = response.read()
        self.status = response.getcode()
        for key, value in response.headers.items():
            # The headers object is dict-like but supports multiple items with
            # the same key, e.g. for Set-Cookie headers.
            key = key.lower()  # field names are not case sensitive
            try:
                self.headers[key].append(value)
            except KeyError:
                # First instance of this key.
                self.headers[key] = value
            except AttributeError:
                # Second instance of this key, start a list.
                self.headers[key] = [self.headers[key], value]
        return


@pytest.fixture
def cgi_local():
    """ Create a pytest fixture for local CGI execution.

    :return: fixture object
    """
    return LocalClient()


@pytest.fixture
def cgi_remote():
    """ Create a pytest fixture for remote CGI execution.

    :return: fixture object
    """
    return RemoteClient()
