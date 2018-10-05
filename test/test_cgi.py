""" Test suite for the cgi module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the package is actually
being tested. If the package is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
from collections import namedtuple
from json import dumps
from json import loads

import pytest
from cgi import *  # tests __all__


# TODO: Need to test fixture itself, not just the underlying object.


@pytest.fixture
def run(monkeypatch):
    """ Mock the subprocess.run() function for testing.

    """
    def mock_run(*args, **kwargs):
        """ Create a mock external process result for testing. """
        attr = "returncode", "stdout"
        MockCompletedProcess = namedtuple("MockCompletedProcess", attr)
        content = dumps({
            "stdin": kwargs.get("input"),
            "env": kwargs.get("env"),
        }).encode()
        header = b"\n".join((
            b"HTTP/1.1 200 OK",
            b"Content-Type: application/json",
            "Content-Length: {:d}".format(len(content)).encode(),
            b"\n",
        ))
        response = header + content
        return MockCompletedProcess(0, response)

    # This requires knowledge of the cgi internals, namely the local alias for
    # subprocess.run().
    monkeypatch.setattr("cgi.run", mock_run)
    return


class RequestTest(object):
    """ Unit tests for the cgi.Request class.

    """
    @pytest.mark.usefixtures("run")
    def test_get(self):
        """ Test the get() method

        """
        request = Request()
        request.get("/path/to/script", {"param": 123})
        assert "application/json" == request.header["Content-Type"]
        content = loads(request.content)
        assert content["env"]["QUERY_STRING"] == "param=123"
        return

    @pytest.mark.usefixtures("run")
    def test_post(self):
        """ Test the post() method

        """
        request = Request()
        request.post("/path/to/script", "content")
        assert request.header["Content-Type"] == "application/json"
        content = loads(request.content)
        assert "content" == content["stdin"]
        return


# Make the module executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
