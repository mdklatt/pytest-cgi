""" Implementation of the `cgi` test fixture.

This will capture the output of an external script executed via a CGI request,
i.e. GET or POST.

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


class _Client(object):
    """ Abstract base class for a CGI script invocation.

    The called script is expected to output an HTTP response.

    :var self.status: HTTP status code
    :var self.header: HTTP header values
    :var self.content: HTTP content
    """
    def __init__(self, script):
        """ Initialize this object.

        :param script: CGI script URL or local path
        """
        self.headers = {}
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


class LocalClient(_Client):
    """ Invoke a local CGI script via the command line.

    :var self.stderr: STDERR output from local script
    """
    def __init__(self, script):
        """ Initialize this object.

        :param script: CGI script path
        """
        super(LocalClient, self).__init__(script)
        self.stderr = None
        return

    def get(self, query):
        """ Execute a GET request.

        :param query: dict-like object of query parameters
        """
        env = {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": urlencode(query, doseq=True),
        }
        self._call(env)
        return

    def post(self, data, mime="text/plain"):
        """ Execute a POST request.

        :param data: text data or dict-like object of query parameters
        :param mime: data MIME type
        """
        if isinstance(data, dict):
            data = urlencode(data, doseq=True).encode()
            mime = "application/x-www-form-urlencoded"
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": len(data),
            "CONTENT_TYPE": mime,
        }
        self._call(env, data)
        return

    def _call(self, env, data=None):
        """ Call a local CGI script via the command line.

        """
        args = split(self._script)
        process = run(args, input=data, stdout=PIPE, stderr=PIPE, env=env)
        self._response(process.stdout)
        self.stderr = process.stderr.decode()
        return

    def _response(self, response):
        """ Parse the response returned by the application.

        :param response: sequence of bytes containing the HTTP response
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
            key, value = (item.strip() for item in line.split(":"))
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


class RemoteClient(_Client):
    """ Invoke a remote CGI script via a URL.

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
        """ Call a CGI script via URL.

        :param url: CGI script URL
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
def cgi(request):
    """ Create a pytest fixture.

    The CGI script to execute is passed in as the parameter of the pytest
    request context.

    :param request: pytest request context
    :return: new fixture object
    """
    script = request.param
    scheme = urlparse(request.param).scheme
    if not scheme:
        fixture = LocalClient(script)
    elif scheme.startswith("http"):  # http/s
        fixture = RemoteClient(script)
    else:
        raise ValueError(f"invalid scheme: {scheme:s}")
    return fixture
