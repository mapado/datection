from setuptools import setup, find_packages

setup(
    name="datection",
    version='1.0.3',
    description='Parse strings and extract normalized temporal data.',
    author=["Balthazar Rouberol"],
    author_email=['balthazar@mapado.com'],
    packages=find_packages(),
    # test_suite='nose.collector'
    # tests_require=['nose'],
    include_package_data=True,
    install_requires=['dateutil'],
)
