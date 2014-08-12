# ri-solr-diff [![Build Status](https://travis-ci.org/discoverygarden/ri-solr-diff.png?branch=1.x)](https://travis-ci.org/discoverygarden/ri-solr-diff)

## Introduction

A utility to identify and resolve differences between a Fedora Commons installation and a Solr index of the contents of the given Fedora Commons installation.

## Requirements

This program requires:

* [requests](http://docs.python-requests.org/)
* [python-dateutil](http://labix.org/python-dateutil)

## Installation

It is recommended to install this utility inside of a [virtualenv](http://virtualenv.readthedocs.org/en/latest/) virtual Python environment.

This program can be relatively easily installed two very similar ways, which should take care of installing the required dependencies:
* If [pip](https://pypi.python.org/pypi/pip) is installed, one can run:
```bash
pip install git+https://github.com/discoverygarden/ri-solr-diff
```
* If just [setuptools](https://pypi.python.org/pypi/setuptools) is installed, one can run:
```bash
git clone https://github.com/discoverygarden/ri-solr-diff
cd ri-solr-diff
python setup.py install
```

It is also possible (though more work) to resolve the dependencies of requests and python-dateutil and to make it available when running `ri-solr-diff.py` on its own (or directly through the interpreter, anyway).

## Usage

Output of `ri-solr-diff.py --help`:
```
usage: ri-solr-diff.py [-h] [--ri RI] [--ri-user RI_USER] [--ri-pass RI_PASS]
                       [--solr SOLR]
                       [--solr-last-modified-field SOLR_LAST_MODIFIED_FIELD]
                       [--gsearch GSEARCH] [--gsearch-user GSEARCH_USER]
                       [--gsearch-pass GSEARCH_PASS]
                       [--query-limit QUERY_LIMIT]
                       (--all | --last-n-days LAST_N_DAYS | --last-n-seconds LAST_N_SECONDS | --since SINCE)
                       [--verbose | --quiet]

Identify and resolve differences between a Fedora Resource and Solr index.

optional arguments:
  -h, --help            show this help message and exit
  --ri RI               URL of the resource index at the host. (default:
                        http://localhost:8080/fedora/risearch)
  --ri-user RI_USER     Username to communicate with resource index. (default:
                        fedoraAdmin)
  --ri-pass RI_PASS     Password to communicate with resource index. (default:
                        islandora)
  --solr SOLR           URL of the Solr end-point. (default:
                        http://localhost:8080/solr)
  --solr-last-modified-field SOLR_LAST_MODIFIED_FIELD
                        The Solr field storing the last modified date of each
                        object. (default: fgs_lastModifiedDate_dt)
  --gsearch GSEARCH     URL of the GSearch end-point. (default:
                        http://localhost:8080/fedoragsearch/rest)
  --gsearch-user GSEARCH_USER
                        Username to communicate with GSearch servelet.
                        (default: fedoraAdmin)
  --gsearch-pass GSEARCH_PASS
                        Password to communicate with GSearch servelet.
                        (default: islandora)
  --query-limit QUERY_LIMIT
                        The number of results which will be fetched from the
                        RI and Solr at a time. (default: 10000)
  --all                 Compare all objects.
  --last-n-days LAST_N_DAYS
                        Compare objects modified in the last n days.
  --last-n-seconds LAST_N_SECONDS
                        Compare objects modified in the last n seconds.
  --since SINCE         Compare objects modified since the given Unix
                        timestamp.
  --verbose, -v         Adjust verbosity of output. More times == more
                        verbose.
  --quiet, -q           Adjust verbosity of output. More times == less
                        verbose.

Exit code will be "0" if everything was up-to-date. If documents were updated,
the exit code will be "1" (though may also be "1" due to runtime errors).
```

## Maintainers/Sponsors

Current maintainers:

* [discoverygarden Inc.](https://github.com/discoverygarden)

## License

[GPLv3](http://www.gnu.org/licenses/gpl-3.0.txt)
