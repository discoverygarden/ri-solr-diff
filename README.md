# ri-solr-diff

## Introduction

A utility to identify and resolve differences between a Fedora Commons installation and a Solr index of the contents of the given Fedora Commons installation. Also provides a utility to re-index a list of PIDs given a file input from stdIn.

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

It is also possible (though more work) to resolve the dependencies of requests and python-dateutil and to make it available when running `ri_solr_diff.py` on its own (or directly through the interpreter, anyway).

## Usage

Output of `ri_solr_diff.py --help`:
```
usage: ri_solr_diff.py [-h] [--ri RI] [--ri-user RI_USER] [--ri-pass RI_PASS]
                       [--solr SOLR]
                       [--solr-last-modified-field SOLR_LAST_MODIFIED_FIELD]
                       [--keep-docs] [--gsearch GSEARCH]
                       [--gsearch-user GSEARCH_USER]
                       [--gsearch-pass GSEARCH_PASS]
                       [--query-limit QUERY_LIMIT]
                       (--all | --last-n-days LAST_N_DAYS | --last-n-seconds LAST_N_SECONDS | --since SINCE | --config-file CONFIG_FILE)
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
  --keep-docs           Keep docs in Solr which do not appear to have related
                        objects in Fedora. The default is to delete Solr
                        documents in this state.
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
  --config-file CONFIG_FILE
                        Provide a JSON configuration file of arguments to be
                        used in place of the CLI.
  --verbose, -v         Adjust verbosity of output. More times == more
                        verbose.
  --quiet, -q           Adjust verbosity of output. More times == less
                        verbose.

Exit code will be "0" if everything was up-to-date. If documents were updated,
the exit code will be "1" (though may also be "1" due to runtime errors). If
config-file is specified and it does not exist "-1" will be exited with.
```
Output of `solr_reindex.py --help`:
```
usage: solr_reindex.py [-h] [--gsearch GSEARCH] [--gsearch-user GSEARCH_USER]
                       [--gsearch-pass GSEARCH_PASS]

Trigger a Solr re-index for a list of PIDs parsed from CSV.

optional arguments:
  -h, --help            show this help message and exit
  --gsearch GSEARCH     URL of the GSearch end-point. (default:
                        http://localhost:8080/fedoragsearch/rest)
  --gsearch-user GSEARCH_USER
                        Username to communicate with GSearch servelet.
                        (default: fedoraAdmin)
  --gsearch-pass GSEARCH_PASS
                        Password to communicate with GSearch servelet.
                        (default: islandora)

Exit code will be "1" if re-index was succcesful, "0" otherwise.
```

Configuration file:

Optionally a JSON configuration file can be specified in place of command-line arguments using the `--config-file` argument. The configuration file will contain key/value pairs of any of the allowed arguments such as:
```json
{
   "ri":"http:\/\/localhost:8080\/fedora\/risearch",
   "ri-user":"fedoraAdmin",
   "ri-pass":"islandora",
   "solr":"http:\/\/localhost:8080\/solr",
   "solr-last-modified-field":"fgs_lastModifiedDate_dt",
   "keep-docs":true,
   "gsearch":"http:\/\/localhost:8080\/fedoragsearch\/rest",
   "gsearch-user":"fedoraAdmin",
   "gsearch-pass":"islandora",
   "query-limit":10000,
   "all":true,
   "verbose":true
}
```

Example of Solr re-indexing: `solr_reindex.py < /mydirectory/file.txt`

## Maintainers/Sponsors

Current maintainers:

* [discoverygarden Inc.](https://github.com/discoverygarden)

Sponsors:

* [United States Department of Agriculture: National Agricultural Library](https://www.nal.usda.gov/)

## License

[GPLv3](http://www.gnu.org/licenses/gpl-3.0.txt)

