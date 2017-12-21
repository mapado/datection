from setuptools import setup, find_packages

setup(
    name="datection",
    version='3.11.0',
    description='Parse strings and extract normalized temporal data.',
    author=["Balthazar Rouberol"],
    author_email=['balthazar@mapado.com'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # private packages
        # public packages
        'python-dateutil',
        'pyparsing==2.0.3',
        'future'
    ],
)
