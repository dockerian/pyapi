"""
# setup module
"""

import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as f:
    README = f.read()
# with open(os.path.join(HERE, 'CHANGES.txt')) as f:
#     CHANGES = f.read()
CHANGES = "Changes"

PREQ = [
    'pyramid',
    'python-keystoneclient',
    'python-swiftclient',
    'pyyaml',
    'responses',
    'sniffer',
    'waitress',
]

PREQ_DEV = [
    'coverage',
    'flake8',
    'mock',
    'nose',
    'pylint',
    'pyramid',
    'tissue',
    'webtest',
    'tox',
]

setup(
    name='codebase',
    version='0.0.1',
    description='Coding demo for Python',
    long_description=README + '\n\n' + CHANGES,
    classifiers=["Programming Language :: Python",
                 "Framework :: Pyramid",
                 "Topic :: Internet :: WWW/HTTP",
                 "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"],
    author='Jason Zhu',
    author_email='yuxin.zhu@hp.com',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=PREQ,
    tests_require=PREQ_DEV,
    test_suite="codebase",
    entry_points="""\
    [paste.app_factory]
    main = codebase:main
    """,
)
