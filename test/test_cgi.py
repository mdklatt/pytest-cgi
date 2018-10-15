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
        header = b"".join((
            b"HTTP/1.1 200 OK\n",
            b"Content-Type: application/json\n",
            "Content-Length: {:d}\n".format(len(content)).encode(),
            b"Set-Cookie: name=cookie1\n",
            b"Set-Cookie: name=cookie2\n",
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
    @pytest.mark.parametrize("cgi", ["/path/to/script"], indirect=True)
    def test_get(self, cgi):
        """ Test the get() method.

        """
        cgi.get({"param": 123})
        assert 200 == cgi.status
        assert "application/json" == cgi.header["content-type"]
        assert ["name=cookie1", "name=cookie2"] == cgi.header["set-cookie"]
        content = loads(cgi.content)
        assert "param=123" == content["env"]["QUERY_STRING"]
        return

    @pytest.mark.usefixtures("run")
    @pytest.mark.parametrize("cgi", ["/path/to/script"], indirect=True)
    @pytest.mark.parametrize("data", ["param=123", {"param": 123}])
    def test_post(self, cgi, data):
        """ Test the post() method.

        The parametrization tests the method with both normal data and query
        parameters.

        """
        cgi.post(data)
        assert 200 == cgi.status
        assert "application/json" == cgi.header["content-type"]
        assert ["name=cookie1", "name=cookie2"] == cgi.header["set-cookie"]
        content = loads(cgi.content)
        assert "param=123" == content["stdin"]
        return


# Make the module executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
