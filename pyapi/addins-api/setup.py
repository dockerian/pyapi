import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

setup(
    name='localapi',
    version='0.0.1',
    description='HP Cloud - Addins Catalog API Service',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Helion Dev',
    author_email='helion.dev@hp.com',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
    tests_require=[i.strip() for i in open("requirements-test.txt").readlines()],
    test_suite="localapi/tests",
    entry_points="""\
    [paste.app_factory]
    main = localapi:main
    """,
)
