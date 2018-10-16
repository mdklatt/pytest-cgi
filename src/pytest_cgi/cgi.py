""" Implementation of the `cgi` test fixture.

This will capture the output of an external application executed via a CGI
request, e.g. GET or POST.

"""
from io import BytesIO
from shlex import split
from subprocess import PIPE
from subprocess import run
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen

import pytest


__all__ = "cgi",


class _CgiFixture(object):
    """ Execute an external CGI application.

    The application is expected to output an HTTP response.

    :var self.status: HTTP status code
    :var self.header: HTTP header values
    :var self.content: HTTP content
    """
    def __init__(self, script):
        """ Initialize this object.

        :param script: location of the CGI script
        """
        self.header = {}
        self.content = None
        self.status = None
        self._script = script
        return

    def get(self, query):
        """ Execute a GET request.

        :param query: dict-like object of query parameters
        """
        raise NotImplementedError

    def post(self, data, mime):
        """ Execute a POST request.

        :param data: binary data or dict-like object of query parameters
        :param mime: data MIME type
        """
        raise NotImplementedError


class _CgiRemote(_CgiFixture):
    """ Execute a remote CGI application.

    The application is called via its URL.

    """
    def get(self, query):
        """ Execute a GET request.

        :param query: dict-like object of query parameters
        """
        url = "?".join((self._script, urlencode(query, doseq=True)))
        self._call(url, "GET")
        return

    def post(self, data, mime=None):
        """ Execute a POST request.

        :param data: binary data or dict-like object of query parameters
        :param mime: data MIME type
        """
        if isinstance(data, dict):
            data = urlencode(data, doseq=True).encode()
            mime = "application/x-www-form-urlencoded"
        headers = {
            "Content-Type": mime,
            "Content-Length": len(data)
        }
        self._call(self._script, "POST", data, headers)
        return

    def _call(self, url, method, data=None, headers=None):
        """

        :param data: binary data
        :param headers: dict-like mapping of HTTP headers
        """
        if not headers:
            headers = {}
        request = Request(url, data, headers, method=method)
        with urlopen(request) as response:
            self.content = response.read()
        self.status = response.getcode()
        for key, value in response.headers.items():
            # The headers object is dict-like but supports multiple items with
            # the same key, e.g. for Set-Cookie headers.
            key = key.lower()  # field names are not case sensitive
            try:
                self.header[key].append(value)
            except KeyError:
                # First instance of this key.
                self.header[key] = value
            except AttributeError:
                # Second instance of this key, start a list.
                self.header[key] = [self.header[key], value]
        return


class _CgiLocal(_CgiFixture):
    """ Execute a local CGI application.

    The fixture simulates a CGI request environment for the application.

    """
    def __init__(self, script):
        """ Initialize this object.

        :param script: path to local CGI script
        """
        super(_CgiLocal, self).__init__(script)
        self._env = {}
        return

    def get(self, query):
        """ Execute a GET request.

        :param query: dict-like object of query parameters
        """
        self._env.update({
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": urlencode(query, doseq=True),
        })
        args = split(self._script)
        process = run(args, stdout=PIPE, stderr=PIPE, env=self._env)
        self._response(process.stdout)
        return

    def post(self, data, mime="text/plain"):
        """ Execute a POST request.

        :param data: text data or dict-like object of query parameters
        :param mime: data MIME type
        """
        if isinstance(data, dict):
            data = urlencode(data, doseq=True)
            mime = "application/x-www-form-urlencoded"
        self._env.update({
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": len(data),
            "CONTENT_TYPE": mime,
        })
        args = split(self._script)
        process = run(args, input=data, stdout=PIPE, stderr=PIPE,
                      env=self._env)
        self._response(process.stdout)
        return

    def _response(self, response):
        """ Parse the response returned by the application.

        :param response: sequence of bytes containing the HTTP response
        """
        # Be lenient about accepting non-standard headers.
        # https://tools.ietf.org/html/rfc7230
        header = []
        with BytesIO(response) as stream:
            for line in stream:
                line = line.decode().strip()
                if not line:
                    break
                header.append(line)
            self.content = stream.read()
        if header[0].lstrip().startswith("HTTP"):
            self.status = int(header[0].split()[1])  # integer status
            header.pop(0)
        for line in header:
            key, value = (item.strip() for item in line.split(":"))
            key = key.lower()  # field names are not case sensitive
            try:
                self.header[key].append(value)
            except KeyError:
                # First instance of this key.
                self.header[key] = value
            except AttributeError:
                # Second instance of this key, start a list.
                self.header[key] = [self.header[key], value]
        return


@pytest.fixture
def cgi(request):
    """ Create a fixture.

    The CGI script to execute is passed in as the parameter of the pytest
    request context.

    :param request: pytest request context
    :return: new fixture object
    """
    script = request.param
    scheme = urlparse(request.param).scheme
    if scheme.startswith("http"):
        return _CgiRemote(script)
    elif scheme:
        raise ValueError(f"invalid scheme: {scheme:s}")
    return _CgiLocal(script)
