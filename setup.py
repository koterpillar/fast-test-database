"""
Setup script.
"""

__version__ = '0.0.1'

from setuptools import setup, find_packages

if __name__ == '__main__':
    with \
            open('requirements.txt') as requirements, \
            open('test_requirements.txt') as test_requirements, \
            open('README.rst') as readme:
        setup(
            name='fast_test_database',
            use_scm_version=True,
            description=(
                'Configure an in-memory database for running Django tests'
            ),
            author='Alexey Kotlyarov',
            author_email='a@koterpillar.com',
            url='https://github.com/koterpillar/fast-test-database',
            long_description=readme.read(),
            classifiers=[
                'License :: OSI Approved :: ' +
                'GNU General Public License v3 or later (GPLv3+)',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 3',
            ],

            packages=find_packages(exclude=['tests']),
            include_package_data=True,

            setup_requires=['setuptools_scm'],

            install_requires=requirements.readlines(),

            test_suite='tests',
            tests_require=test_requirements.readlines(),
        )
