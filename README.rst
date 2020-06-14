##########
pytest-cgi
##########

|travis.png|

The `pytest-cgi`_ plugin is useful for black box testing of CGI scripts using
`pytest`_. Install the plugin as a normal Python package, and the ``cgi_local``
and ``cgi_remote`` fixtures will become available. These fixutres will simulate
CGI calls to local or remote applications, respectively.

For each fixture, a script is invoked via the ``get()`` or ``post()`` methods,
and its captured output is available in the ``status``, ``headers``, and
``content`` attributes. The ``cgi_local`` fixture also has a ``stderr``
attribute.


.. code-block:: python

    import pytest  # `cgi` fixture is loaded automatically

    def test_post(cgi_remote):
        """ Test a remote version of a script.

        """
        # For post(), can send form values or binary data with a MIME type.
        script = "https://www.example.com/script.cgi"
        cgi_remote.post(script, {"param": "abc"})  # application/x-www-form-urlencoded
        assert cgi_remote.status == 200
        assert cgi_remote.headers["content-type"] == "text/plain"
        assert cgi_remote.content.decode() == "param: 'abc'"
        return

.. |travis.png| image:: https://travis-ci.org/mdklatt/pytest-cgi.svg?branch=master
   :alt: Travis CI build status
   :target: `travis`_
.. _travis: https://travis-ci.org/mdklatt/pytest-cgi
.. _pytest-cgi: http://github.com/mdklatt/pytest-cgi
.. _pytest: http://pytest.org
