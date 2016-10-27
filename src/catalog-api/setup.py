import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
# with open(os.path.join(here, 'CHANGES.txt')) as f:
#     CHANGES = f.read()
CHANGES = "Changes"

requires = [
    'pyramid',
    'python-keystoneclient',
    'python-swiftclient',
    'waitress',
    'nose',
    'coverage',
    'mock',
    'webtest',
    'tissue',
    'pyyaml',
    ]

setup(
    name='globalapi',
    version='0.0.2',
    description='HP Cloud - Global Catalog API Service',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
      "Programming Language :: Python",
      "Framework :: Pyramid",
      "Topic :: Internet :: WWW/HTTP",
      "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author = 'Helion Dev',
    author_email = 'helion.dev@hp.com',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="globalapi",
    entry_points="""\
    [paste.app_factory]
    main = globalapi:main
    """,
    )
