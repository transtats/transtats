import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open(os.path.join(os.path.dirname(__file__), "requirements/base.txt"), 'rb') as require:
    REQUIRE = require.read().decode('utf-8').splitlines() + ['setuptools']

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='transanalytics',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIRE,
    license='GPLv3 License',
    description='An analytics to translation statistics',
    long_description=README,
    url='https://transanalytics-suanand.rhcloud.com',
    author='Sundeep Anand',
    author_email='suanand@redhat.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9.5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)