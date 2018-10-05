""" Test suite for the cgi fixture.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the package is actually
being tested. If the package is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
from json import dumps
from json import loads

import pytest


@pytest.fixture
def run(monkeypatch):
    """ Mock the subprocess.run() function for testing.

    """
    def mock_run(*_, **kwargs):
        """ Create a mock external process result for testing. """
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
        return _MockCompletedProcess(response)

    # This requires knowledge of the pytest_cgi.cgi internals, namely the local
    # alias for subprocess.run().
    monkeypatch.setattr("pytest_cgi.cgi.run", mock_run)
    return


class _MockCompletedProcess(object):
    """ Mock a subprocess.CompleteProcess instance.

    """
    def __init__(self, stdout):
        """ Initialize this object.

        :param stdout: sequence of bytes sent to STDOUT
        """
        self.stdout = stdout
        self.returncode = 0
        self.check_returncode = lambda: None  # always a "success"
        return


class CgiFixtureTest(object):
    """ Unit tests for the cgi fixture.

    This requires the plugin to be installed into the test environment using
    setup.py; it is not sufficient to add the source directory to PYTHONPATH.

    """
    @pytest.mark.usefixtures("run")
    def test_get(self, cgi):
        """ Test the get() method.

        """
        cgi.get("/path/to/script", {"param": 123})
        assert 200 == cgi.status
        assert "application/json" == cgi.header["Content-Type"]
        content = loads(cgi.content)
        assert "param=123" == content["env"]["QUERY_STRING"]
        return

    @pytest.mark.usefixtures("run")
    def test_post(self, cgi):
        """ Test the post() method.

        """
        cgi.post("/path/to/script", "content")
        assert 200 == cgi.status
        assert "application/json" == cgi.header["Content-Type"]
        content = loads(cgi.content)
        assert "content" == content["stdin"]
        return


# Make the module executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
