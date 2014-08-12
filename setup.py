#!/usr/bin/env python

from distutils.core import setup

setup(
  name='Resource Index/Solr Sync',
  version='1.0',
  description='Sync Solr index by examining Resource Index.',
  long_description='Ensure a Solr index is up-to-date with a Fedora Commons installation, based on the contents of the Resource Index.',
  author='discoverygarden Inc.',
  author_email='dev@discoverygarden.ca',
  scripts=['bin/ri-solr-diff.py'],
  requires=[
    'requests',
    'dateutil',
  ],
)
