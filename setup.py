import datection
from setuptools import setup, find_packages

setup(
    name="datection",
    version=datection.__version__,
    description='Parse strings and extract normalized temporal data.',
    author=["Balthazar Rouberol"],
    author_email=['balthazar@mapado.com'],
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose'],
    )
