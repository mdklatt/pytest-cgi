""" Test suite for the cgi fixture.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the package is actually
being tested. If the package is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
from http.client import HTTPMessage
from json import dumps
from json import loads
from urllib.parse import urlparse

import pytest


class _MockCompletedProcess(object):
    """ Mock a subprocess.CompleteProcess instance.

    """
    def __init__(self, stdout):
        """ Initialize this object.

        :param stdout: sequence of bytes sent to STDOUT
        """
        self.stdout = stdout
        self.stderr = b"unexpected error"
        self.returncode = 0
        self.check_returncode = lambda: None  # always a "success"
        return


class _MockResponse(object):
    """ A mock urllib.response.

    """
    def __init__(self, data, headers):
        """ Initialize this object.

        """
        self.headers = headers
        self.read = lambda: data
        self.getcode = lambda: 200
        return

    def __enter__(self):
        """ Enter a runtime context.

        """
        return self

    def __exit__(self, *args):
        """ Exit a runtime context.

        """
        return


@pytest.fixture
def run(monkeypatch):
    """ Mock the subprocess.run() function for testing.

    """
    def mock_run(*_, **kwargs):
        """ Create a mock external process result for testing. """
        try:
            data = kwargs.get("input").decode()
        except AttributeError:
            data = None
        content = dumps({
            "data": data,
            "query": kwargs["env"].get("QUERY_STRING"),
        }).encode()
        headers = b"".join((
            b"HTTP/1.1 200 OK\n",
            b"Content-Type: application/json\n",
            b"Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\n",
            "Content-Length: {:d}\n".format(len(content)).encode(),
            b"Set-Cookie: name=cookie1\n",
            b"Set-Cookie: name=cookie2\n",
            b"\n",
        ))
        response = headers + content
        return _MockCompletedProcess(response)

    # This requires knowledge of the pytest_cgi.cgi internals, namely the local
    # alias for subprocess.run().
    monkeypatch.setattr("pytest_cgi.cgi.run", mock_run)
    return


@pytest.fixture
def urlopen(monkeypatch):
    """ Mock the urlopen() function for testing.

    """
    def mock_urlopen(request, *_, **__):
        """ Create a mock HTTP response. """
        # request has data, header, method
        data = dumps({
            "data": request.data.decode() if request.data else None,
            "query": urlparse(request.full_url).query
        }).encode()
        fields = (
            ("Content-Type", "application/json"),
            ("Last-Modified", "Thu, 01 Jan 1970 00:00:00 GMT"),
            ("Set-Cookie", "name=cookie1"),
            ("Set-Cookie", "name=cookie2"),
        )
        headers = HTTPMessage()
        for key, value in fields:
            headers[key] = value
        return _MockResponse(data, headers)

    # This requires knowledge of the pytest_cgi.cgi internals, namely the local
    # alias for urllib.request.urlopen().
    urlopen = "pytest_cgi.cgi.urlopen"
    monkeypatch.setattr(urlopen, mock_urlopen)
    return


class CgiFixtureTest(object):
    """ Unit tests for the cgi fixture.

    This requires the plugin to be installed into the test environment using
    setup.py; it is not sufficient to add the source directory to PYTHONPATH.

    """
    @pytest.mark.usefixtures("run", "urlopen")
    @pytest.mark.parametrize("cgi", ["/cgi", "https://www.example.com/cgi"],
                             indirect=True)
    def test_get(self, cgi):
        """ Test the get() method.

        """
        cgi.get({"param": 123})
        assert cgi.status == 200
        assert cgi.headers["content-type"] == "application/json"
        assert cgi.headers["set-cookie"] == ["name=cookie1", "name=cookie2"]
        content = loads(cgi.content)
        assert content["query"] == "param=123"
        assert not content["data"]
        return

    @pytest.mark.usefixtures("run", "urlopen")
    @pytest.mark.parametrize("cgi", ["/cgi", "https://www.example.com/cgi"],
                             indirect=True)
    @pytest.mark.parametrize("data", [b"param=123", {"param": 123}])
    def test_post(self, cgi, data):
        """ Test the post() method.

        The parametrization tests the method with both normal data and query
        parameters.

        """
        cgi.post(data)
        assert cgi.status == 200
        assert cgi.headers["content-type"] == "application/json"
        assert cgi.headers["set-cookie"] == ["name=cookie1", "name=cookie2"]
        content = loads(cgi.content)
        assert content["data"] == "param=123"
        assert not content["query"]
        return


# Make the module executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
