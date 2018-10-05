""" Setup script for the pytest-cgi plugin.

The implementation is installed as a normal Python package, and an entry point
is created to identify the package to pytest as a plugin.

"""
from distutils import log
from itertools import chain
from os import walk
from os.path import join
from subprocess import check_call
from subprocess import CalledProcessError

from setuptools import Command
from setuptools import find_packages
from setuptools import setup


_CONFIG = {
    "name": "pytest-cgi",
    "author": "Michael Klatt",
    "author_email": "mdklatt@alumni.ou.edu",
    "license": "MIT",
    "url": "https://github.com:mdklatt/pytest-cgi",
    # "package_dir": {"": "src"},
    # "packages": find_packages("src"),
    "pymodules": ("src/pytest_cgi",),
    "entry_points": {
        "pytest11": ["cgi = pytest_cgi"],
    },
    "install_requires": ["pytest>=3.5.0"]  # TODO: get from requirements?
}


def _version():
    """ Get the local package version.

    """
    path = join("src", _CONFIG["name"], "__version__.py")
    namespace = {}
    with open(path) as stream:
        exec(stream.read(), namespace)
    return namespace["__version__"]


def main():
    """ Execute the setup commands.

    """
    _CONFIG.update({
        # "version" = _version()  # FIXME: need __version__.py
    })
    setup(**_CONFIG)
    return 0


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
