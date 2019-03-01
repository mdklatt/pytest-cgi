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
the ``get()`` or ``post()`` method, and its captured output is available in the
``status``, ``headers``, and ``content`` attributes. For local scripts, a
``stderr`` attribute is also available.


.. code-block:: python

    import pytest  # `cgi` fixture is loaded automatically

    _SCRIPTS = "/script.cgi", "https://www.example.com/script.cgi"

    @pytest.mark.parametrize("cgi", _SCRIPTS, indirect=True)
    def test_post(cgi):
        """ Test a local and remote version of a script.

        """
        # For post(), can send form values or binary data with a MIME type.
        cgi.post({"param": "abc"})  # application/x-www-form-urlencoded
        assert cgi.status == 200
        assert cgi.headers["content-type"] == "text/plain"
        assert cgi.content.decode() == "param: 'abc'"
        return

