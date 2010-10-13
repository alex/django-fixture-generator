import os

from setuptools import setup, find_packages

from fixture_generator import VERSION


f = open(os.path.join(os.path.dirname(__file__), 'README.txt'))
readme = f.read()
f.close()

setup(
    name='django-fixture-generator',
    version=".".join(map(str, VERSION)),
    description='django-fixture-generator is a reusable django application to make writing fixtures not suck.',
    long_description=readme,
    author='Alex Gaynor',
    author_email='alex.gaynor@gmail.com',
    url='http://github.com/alex/django-fixture-generator/tree/master',
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    test_suite='runtests.runtests'
)

