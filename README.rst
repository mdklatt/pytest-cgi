##########
pytest-cgi
##########

.. |travis.png| image:: https://travis-ci.org/mdklatt/pytest-cgi.png?branch=master
   :alt: Travis CI build status
   :target: `travis`_
.. _travis: https://travis-ci.org/mdklatt/pytest-cgi
.. _pytest-cgi: http://github.com/mdklatt/pytest-cgi
.. _pytest: http://pytest.org


The `pytest-cgi`_ plugin is useful for black box testing of CGI applications
using `pytest`_. Install the plugin as a normal Python packages, and the
``cgi`` fixture will become available.

This fixture can be used to simulate a CGI call to an external application and
capture its output. The CGI applications is expected to return a standard HTTP
response.


.. code-block:: python

    import pytest  # loads `cgi` fixture

    def test_script(cgi):
        """ Example of testing with the `cgi` fixture.

        """
        # Tests call of the form script.cgi?param=abc&param=123
        cgi.get("/path/to/script.cgi", {"param": "abc", "param": 123})
        assert 200 == cgi.status
        assert "text/plain" == cgi.header["Content-Type"]
        assert
        assert b"called with params 'abc' and '123'" == cgi.content
        return

