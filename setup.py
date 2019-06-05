""" Setup script for the pytest-cgi plugin.

The implementation is installed as a normal Python package, and an entry point
is created to expose the package to pytest as a plugin.

"""
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


_config = {
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
    "install_requires": [
        "pytest>=4.0"
    ]
}


def main() -> int:
    """ Execute the setup command.

    """
    def version():
        """ Get the local package version. """
        namespace = {}
        path = Path("src", "pytest_cgi", "__version__.py")
        exec(path.read_text(), namespace)
        return namespace["__version__"]

    _config.update({
        "version": version(),
    })
    setup(**_config)
    return 0


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
