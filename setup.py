#!/usr/bin/env python

from distutils.core import setup

setup(
  name='Resource Index/Solr Sync',
  version='1.0',
  description='Ensure a Solr index is up-to-date with a Fedora Commons installation, based on the contents of the Resource Index.',
  author='discoverygarden Inc.',
  author_email='dev@discoverygarden.ca',
  scripts=['bin/ri-solr-diff'],
  requires=[
    'requests',
    'dateutil',
  ],
)
