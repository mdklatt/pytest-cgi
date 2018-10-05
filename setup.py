""" Setup script for the pytest-cgi plugin.

The implementation is installed as a normal Python package, and an entry point
is created to expose the package to pytest as a plugin.

"""
from os.path import join
from setuptools import find_packages
from setuptools import setup


_CONFIG = {
    "name": "pytest-cgi",
    "author": "Michael Klatt",
    "author_email": "mdklatt@alumni.ou.edu",
    "license": "MIT",
    "url": "https://github.com:mdklatt/pytest-cgi",
    "package_dir": {"": "src"},
    "packages": find_packages("src"),
    "entry_points": {
        "pytest11": ["cgi = pytest_cgi.cgi"],
    },
    "install_requires": ["pytest>=3.5.0"]  # TODO: get from requirements?
}


def _version():
    """ Get the local package version.

    """
    path = join("src", "pytest_cgi", "__version__.py")
    namespace = {}
    with open(path) as stream:
        exec(stream.read(), namespace)
    return namespace["__version__"]


def main():
    """ Execute the setup commands.

    """
    _CONFIG.update({
        "version": _version()
    })
    setup(**_CONFIG)
    return 0


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
