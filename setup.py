"""
Minimal setup.py to allow for local installation in the development environment
with `pip install -e .`
"""
import io
import re
from os import path

from setuptools import setup, find_packages

# Get the version from rxn_actions/__init__.py
# Adapted from https://stackoverflow.com/a/39671214
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open('paragraph2actions/__init__.py', encoding='utf_8_sig').read()
).group(1)

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='paragraph2actions',
    version=__version__,
    url='https://rxn.res.ibm.com',
    author='IBM RXN',
    author_email='noreply@zurich.ibm.com',
    description='Convert experimental procedures to sequences of actions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'attrs>=19.1.0',
        'click>=7.0',
        'nltk>=3.4.5',
        'OpenNMT-Py>=1.1.1',
        'sentencepiece>=0.1.83',
        'textdistance>=4.1.5',
    ],
)
