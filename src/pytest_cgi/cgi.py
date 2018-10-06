""" Implementation of the `cgi` test fixture.

This will capture the output of an external application executed via a CGI
request, e.g. GET or POST.

"""
from io import BytesIO
from shlex import split
from subprocess import PIPE
from subprocess import run
from urllib.parse import urlencode

import pytest


__all__ = "cgi",


class _CgiFixture(object):
    """ Execute an external CGI application.

    The application is expected to write an HTTP response to STDOUT.

    :var self.status: HTTP status code
    :var self.header: HTTP header values
    :var self.content: HTTP content
    """
    def __init__(self):
        """ Initialize this object.

        """
        self.header = {}
        self.content = None
        self.status = None
        self._env = {}
        return

    def get(self, script, query):
        """ Execute a GET request.

        :param script: path to CGI application
        :param query: dict-like object of query parameters
        """
        self._env.update({
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": urlencode(query, doseq=True),
        })
        args = split(script)
        process = run(args, stdout=PIPE, stderr=PIPE, env=self._env)
        self._response(process.stdout)

    def post(self, script, data, mime="text/plain"):
        """ Execute a POST request.

        :param script: path to CGI application
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
        args = split(script)
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
def cgi():
    """ Factory function for a _CgiFixture object.

    :return: new _CgiFixture object
    """
    return _CgiFixture()
