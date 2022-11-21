from setuptools import setup, find_packages

setup(
    name="datection",
    version='4.0.7',
    description='Parse strings and extract normalized temporal data.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires='>=3.5',
    author='Balthazar Rouberol',
    maintainer='Julien Deniau',
    maintainer_email='julien.deniau@mapado.com',
    url='https://github.com/mapado/datection',
    packages=find_packages(),
    license='MIT',
    install_requires=[
        # private packages
        # public packages
        'python-dateutil',
        'pyparsing==2.0.3',
        'future'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)
