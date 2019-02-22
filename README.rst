##########
pytest-cgi
##########

.. |badge| image:: https://travis-ci.org/mdklatt/pytest-cgi.svg?branch=master
   :alt: Travis CI build status
   :target: `travis`_
.. _travis: https://travis-ci.org/mdklatt/pytest-cgi
.. _pytest-cgi: http://github.com/mdklatt/pytest-cgi
.. _pytest: http://pytest.org

|badge|

The `pytest-cgi`_ plugin is useful for black box testing of CGI scripts using
`pytest`_. Install the plugin as a normal Python package, and the ``cgi``
fixture object will become available. This fixture will invoke a remote script
via its URL or a local script via a simulated CGI request.

The fixture takes one parameter, the script location. The script is invoked via
the ``get()`` or ``post()`` method, and the captured output will be available
in the ``status``, ``headers``, and ``content`` attributes.


.. code-block:: python

    import pytest  # loads `cgi` fixture

    @pytest.mark.parametrize("cgi", ["/cgi", "https://www.example.com/cgi"],
                             indirect=True)
    def test_post(cgi):
        """ Test a local and remote script with the `cgi` fixture.

        """
        # For post(), can send form values or binary data with a MIME type.
        cgi.post({"param": "abc"})
        assert 200 == cgi.status
        assert "text/plain" == cgi.headers["content-type"]
        assert "called with param 'abc'" == cgi.content.decode()
        return

