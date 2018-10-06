""" Implementation of the `cgi` test fixture.

This will capture the output of an external application executed via a CGI
request, e.g. GET or POST.

"""
from io import StringIO
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
        process.check_returncode()
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
        process.check_returncode()
        self._response(process.stdout)
        return

    def _response(self, response):
        """ Parse the response returned by the application.

        :param response: sequence of bytes containing the HTTP response
        :return:
        """
        # TODO: Surely there's a built-in module that will do this?
        header, self.content = response.split(b"\r\n", 1)
        lines = header.decode().strip().split("\n")
        self.status = int(lines[0].split()[1])  # integer status
        for line in lines[1:]:
            key, value = (item.strip() for item in line.split(":"))
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
