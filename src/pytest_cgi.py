""" Test fixture for executing a CGI application.

"""
from io import StringIO
from shlex import split
from subprocess import PIPE
from subprocess import run
from urllib.parse import urlencode

import pytest


__all__ = "cgi", "Request"


__version__ = "0.1.0dev1"  # PEP 440


class Request(object):
    """ Execute an external application using a CGI request.

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

        :param script: path to executable CGI script
        :param query: dict-like object of query parameters
        """
        # TODO: The script path should be an object-level attribute.
        self._env.update({
            "QUERY_STRING": urlencode(query, doseq=True),
        })
        args = split(script)
        process = run(args, stdout=PIPE, stderr=PIPE, env=self._env)
        self._response(process.stdout)

    def post(self, script, data, mime="text/plain"):
        """ Execute a POST request.

        :param script: path to executable CGI script
        :param data: text data or dict-like object of query parameters
        :param mime: data MIME type
        """
        # TODO: The script path should be an object-level attribute.
        if isinstance(data, dict):
            data = urlencode(data, doseq=True)
            mime = "application/x-www-form-urlencoded"
        self._env.update({
            "CONTENT_LENGTH": len(data),
            "CONTENT_TYPE": mime,
        })
        args = split(script)
        process = run(args, input=data, stdout=PIPE, stderr=PIPE,
                      env=self._env)
        # TODO: Check return code.
        self._response(process.stdout)
        return

    def _response(self, message):
        """ Parse the HTTP response returned by the CGI script.

        :param message:
        :return:
        """
        # Surely there's a library that will do this? The HTTPResponse class in
        # http.client does more than just parse a response, and is not supposed
        # to be used directly.
        with StringIO(message.decode()) as stream:
            # FIXME: Won't work for binary content.
            version, self.status, status = stream.readline().strip().split()
            while True:
                # Parse response header.
                line = stream.readline().strip()
                if not line:
                    # End of header.
                    break
                key, value = (item.strip() for item in line.split(":"))
                try:
                    self.header[key].append(value)
                except KeyError:
                    # First instance of this key.
                    self.header[key] = value
                except AttributeError:
                    # Second instance of this key, start a list.
                    self.header[key] = [self.header[key], value]
            self.content = stream.read()
        return


@pytest.fixture
def cgi():
    """ Request factory.

    :return: Request object
    """
    # TODO: Get script name from config? Fixture parameters?
    return Request()
