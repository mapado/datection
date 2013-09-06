import re

from os.path import dirname, join
from setuptools import setup, find_packages


version = re.search("__version__ = '([^']+)'", open(
    join(dirname(__file__), 'datection', '__init__.py')
).read().strip()).group(1)

setup(
    name="datection",
    version=version,
    description='Parse strings and extract normalized temporal data.',
    author=["Balthazar Rouberol"],
    author_email=['balthazar@mapado.com'],
    packages=find_packages(),
    # test_suite='nose.collector'
    # tests_require=['nose'],
    include_package_data=True
)
