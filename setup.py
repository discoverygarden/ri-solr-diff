from setuptools import setup

setup(
  name='ri-solr-diff',
  version='1.0',
  description='Sync Solr index by examining Resource Index.',
  long_description='Ensure a Solr index is up-to-date with a Fedora Commons installation, based on the contents of the Resource Index.',
  author='Adam Vessey',
  author_email='adam@discoverygarden.ca',
  maintainer='discoverygarden Inc.',
  maintainer_email='dev@discoverygarden.ca',
  url='http://github.com/discoverygarden/ri-solr-diff',
  scripts=[
    'bin/ri_solr_diff.py',
    'bin/solr_reindex.py',
  ],
  install_requires=[
    'requests',
    'python-dateutil'
  ]
)
