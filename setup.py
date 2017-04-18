#!/usr/bin/env python

import os
import setuptools
import mpesa

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setuptools.setup(
    name="python-mpesa",
    version=mpesa.__version__,
    packages=setuptools.find_packages(),
    include_package_data=True,
    license='BSD',
    description='M-Pesa API G2 Python adapter',
    long_description=README,
    url="http://onepercentclub.com",
    author="Loek van Gent",
    author_email="hallo@loekvan.gent",
    install_requires=[
        'suds'
    ],
    tests_require=[
        'nose'
    ],
    test_suite='nose.collector',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
