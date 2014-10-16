from setuptools import setup, find_packages

setup(
    name="datection",
    version='2.3.1',
    description='Parse strings and extract normalized temporal data.',
    author=["Balthazar Rouberol"],
    author_email=['balthazar@mapado.com'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # private packages
        'python-dateutil==2.1.1',
        # public packages
        'pyparsing'
    ],
)
