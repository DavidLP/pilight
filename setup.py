#!/usr/bin/env python
from setuptools import setup, find_packages  # This setup relies on setuptools since distutils is insufficient and badly hacked code

version = '0.1.1'
author = 'David-Leon Pohl'
author_email = 'David-Leon.Pohl@rub.de'

setup(
    name='pilight',
    version=version,
    description='A pure python module to connect to a pilight daemon to send and receive commands.',
    url='https://github.com/DavidLP/pilight',
    license='MIT License',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    packages=find_packages(),
    include_package_data=True,  # Accept all data files and directories matched by MANIFEST.in or found in source control
    keywords=['pilight', '433', 'light'],
    platforms='any'
)
