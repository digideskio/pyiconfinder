#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


packages = [
    'pyiconfinder',
]

requires = [
    'requests>=1.0.0,<2.4.0',
    'six',
    'enum34',
]

tests_require = [
    'nose',
    'rednose',
    'flake8',
]

setup(
    name='pyiconfinder',
    version='1.0.0',
    description='Iconfinder API library for Python',
    author='Iconfinder',
    author_email='support@iconfinder.com',
    url='https://www.iconfinder.com/',
    packages=packages,
    package_data={
        '': ['LICENSE'],
        'pyiconfinder': ['pyiconfinder/wildcard.iconfinder.com.pem'],
    },
    package_dir={'pyiconfinder': 'pyiconfinder'},
    include_package_data=True,
    tests_require=tests_require,
    install_requires=requires,
    license=open('LICENSE').read(),
    zip_safe=True,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
