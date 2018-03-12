#!/usr/bin/env python

import itertools
import dateutil.parser
import time
import requests
import argparse
import logging
import json
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%s', level=logging.INFO)

# requests is kind of noisy by default... Let's shut it up.
logging.getLogger('requests').setLevel(logging.WARNING)

parser = argparse.ArgumentParser(
    description='Identify and resolve differences between a Fedora Resource and Solr index.',
    epilog='Exit code will be "0" if everything was up-to-date. If documents were updated, the exit code will be "1" (though may also be "1" due to runtime errors). If config-file is specified and it does not exist "-1" will be exited with.'
)
# Connection arguments
parser.add_argument('--ri', default="http://localhost:8080/fedora/risearch", help='URL of the resource index at the host. (default: %(default)s)')
parser.add_argument('--ri-user', default='fedoraAdmin', help='Username to communicate with resource index. (default: %(default)s)')
parser.add_argument('--ri-pass', default='islandora', help='Password to communicate with resource index. (default: %(default)s)')
parser.add_argument('--solr', default="http://localhost:8080/solr", help='URL of the Solr end-point. (default: %(default)s)')
parser.add_argument('--solr-last-modified-field', default='fgs_lastModifiedDate_dt', help='The Solr field storing the last modified date of each object. (default: %(default)s)')
parser.add_argument('--keep-docs', default=False, action='store_true', help='Keep docs in Solr which do not appear to have related objects in Fedora. The default is to delete Solr documents in this state.')
parser.add_argument('--gsearch', default="http://localhost:8080/fedoragsearch/rest", help="URL of the GSearch end-point. (default: %(default)s)")
parser.add_argument('--gsearch-user', default='fedoraAdmin', help='Username to communicate with GSearch servelet. (default: %(default)s)')
parser.add_argument('--gsearch-pass', default='islandora', help='Password to communicate with GSearch servelet. (default: %(default)s)')
parser.add_argument('--query-limit', default=10000, type=int, help='The number of results which will be fetched from the RI and Solr at a time. (default: %(default)s)')

# Application switches
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--all', help='Compare all objects.', action='store_true')
group.add_argument('--last-n-days', type=int, help='Compare objects modified in the last n days.')
group.add_argument('--last-n-seconds', type=int, help='Compare objects modified in the last n seconds.')
group.add_argument('--since', type=int, help='Compare objects modified since the given Unix timestamp.')
group.add_argument('--config-file', help='Provide a JSON configuration file of arguments to be used in place of the CLI.')

log_group = parser.add_mutually_exclusive_group()
log_group.add_argument('--verbose', '-v', default=0, action='count', help='Adjust verbosity of output. More times == more verbose.')
log_group.add_argument('--quiet', '-q', default=0, action='count', help='Adjust verbosity of output. More times == less verbose.')


class ri_generator:
    """Generator object for Resource Index."""

    def __init__(self, url, user=None, password=None, start=None, limit=10000):
        """
        Constructor; stash state.

        Arguments:
        url -- URL to the end-point. Likely something like
               "http://localhost:8080/fedora/risearch".
        user -- User name to use to connect.
        password -- Password to use to connect.
        start -- Either None or a full ISO 8601 timestamp, like:
                 "2014-07-12T20:18:12.023Z"
        limit -- The number of results returned at a time; will affect
                 memory usage.
        """
        self.url = url
        self.user = user
        self.password = password
        self.start = start
        self.limit = limit

    def __iter__(self):
        """
        Iterator protocol implementation.

        Yields 2-tuples, each consisting of a PID and a struct_time.
        """
        replacements = {
            'filter': ''
        }
        if self.start is not None:
            replacements['filter'] = 'FILTER(?timestamp >= "{0}"^^<http://www.w3.org/2001/XMLSchema#dateTime>)'.format(self.start)

        # XXX: The OPTIONAL/?exclude bit prevents documents we usually avoid
        # indexing into Solr from being selected. Since they should not be in
        # the Solr index, we do not need to adjust the Solr query to account
        # for them.
        query = '''
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?obj ?timestamp
FROM <#ri>
WHERE {{
  ?obj <fedora-model:hasModel> <info:fedora/fedora-system:FedoraObject-3.0> ;
       <fedora-model:state> <fedora-model:Active> ;
       <fedora-view:lastModifiedDate> ?timestamp .
  OPTIONAL {{
    ?obj <fedora-view:disseminates> ?exclude .
    {{
      ?exclude <fedora-view:disseminationType> <info:fedora/*/DS-COMPOSITE-MODEL> .
    }} UNION {{
      ?exclude <fedora-view:disseminationType> <info:fedora/*/METHODMAP> .
    }}
  }}
  FILTER(!bound(?exclude))
  {filter}
}}
ORDER BY ?timestamp ?obj
'''
        data = {
            'type': 'tuples',
            'format': 'json',
            'lang': 'sparql',
            'query': query.format(**replacements),
            'limit': self.limit
        }
        s = requests.Session()
        s.auth = (self.user, self.password)
        r = s.post(self.url, data=data)

        while r.status_code == requests.codes.ok:
            # XXX: Seems to be some weird encoding issue preventing r.json()
            # from working?
            query_result = json.loads(r.text)

            if len(query_result['results']) == 0:
                break

            for result in query_result['results']:
                yield (result['obj'].split('info:fedora/')[1], dateutil.parser.parse(result['timestamp']))

            # Grab the last timestamp, to start from it.
            self.start = query_result['results'][-1]['timestamp']
            start_pid = query_result['results'][-1]['obj']

            replacements['filter'] = 'FILTER((?timestamp = "{0}"^^xsd:dateTime && xsd:string(?obj) > "{1}"^^xsd:string) || ?timestamp > "{0}"^^xsd:dateTime)'.format(self.start, start_pid)
            data['query'] = query.format(**replacements)
            r = s.post(self.url, data=data)
        else:
            raise Exception('RI query failed with HTTP code {0}. Body: {1}'.format(r.status_code, r.text))


class solr_generator:
    """Generator object for Solr index."""

    def __init__(self, url, field, start=None, limit=10000):
        """
        Constructor; stash state.

        Arguments:
        url -- URL to the end-point. Likely something like
               "http://localhost:8080/solr".
        field -- The Solr field which holds the last modified date of
                 records.
        start -- Either None or a full ISO 8601 timestamp, like:
                 "2014-07-12T20:18:12.023Z"
        limit -- The number of results returned at a time; will affect
                 memory usage.
        """
        self.base_url = url
        self.url = "{base_url}/select".format(base_url=url)
        self.field = field
        self.start = start
        self.limit = limit

    def __iter__(self):
        """
        Iterator protocol implementation.

        Yields 2-tuples, each consisting of a PID and a struct_time.
        """
        params = {
            'q': '*:*',
            'sort': '{last_modified_field} asc, PID asc'.format(last_modified_field=self.field),
            'wt': 'json',
            'fl': 'PID {last_modified_field}'.format(last_modified_field=self.field),
            'rows': self.limit
        }
        if self.start is not None:
            params['fq'] = ["{0}:{{{1} TO *}}".format(self.field, self.start)]

        r = requests.post(self.url, data=params)

        while r.status_code == requests.codes.ok:
            # XXX: Seems to be some weird encoding issue preventing r.json()
            # from working?
            query_results = json.loads(r.text)

            if query_results['response']['numFound'] == 0 or len(query_results['response']['docs']) == 0:
                break

            for result in query_results['response']['docs']:
                yield (result['PID'], dateutil.parser.parse(result[self.field]))

            # Grab the last timestamp, to start from it.
            self.start = query_results['response']['docs'][-1][self.field]
            start_pid = query_results['response']['docs'][-1]['PID']

            params['fq'] = ['({0}:"{1}" AND PID:{{{2} TO *}}) OR {0}:{{{1} TO *}}'.format(self.field, self.start, start_pid)]
            r = requests.post(self.url, data=params)
        else:
            raise Exception('Solr query failed with HTTP code {0}.'.format(r.status_code))


class gsearch:
    """Helper class for prodding GSearch."""

    def __init__(self, url, user, password, keep_docs):
        """
        Constructor; stash state.

        Arguments:
        url -- URL to the end-point. Likely something like
               "http://localhost:8080/fedoragsearch/rest".
        user -- User name to use to connect.
        password -- Password to use to connect.
        """
        self.url = url
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)
        self.updated = False
        self.keep_docs = keep_docs

    def update_pid(self, pid):
        """Call to GSearch to update the given PID."""
        if not self.updated:
            self.updated = True

        data = {
            'operation': 'updateIndex',
            'action': 'fromPid',
            'value': pid
        }
        logging.debug('Attempting to update {0}...'.format(pid))
        r = self.session.post(self.url, data=data)
        if r.status_code == requests.codes.ok and not 'Object not found in low-level storage' in r.text:
            logging.debug('Updated {0}'.format(pid))
            logging.info(pid)
        else:
            reason = 'Not in Fedora' if r.status_code == requests.codes.ok and 'Object not found in low-level storage' in r.text else 'HTTP code {0}'.format(r.status_code)
            logging.debug('Failed to update {0} ({1}).'.format(pid, reason))
            if not self.keep_docs:
                self.delete_pid(pid)

    def delete_pid(self, pid):
        """Call to GSearch to delete the given PID."""
        if not self.updated:
            self.updated = True

        data = {
            'operation': 'updateIndex',
            'action': 'deletePid',
            'value': pid
        }
        logging.debug('Attempting to delete {0}...'.format(pid))
        r = self.session.post(self.url, data=data)
        if r.status_code == requests.codes.ok:
            logging.debug('Deleted {0}'.format(pid))
        else:
            logging.debug('Failed to delete {0} (HTTP code {1}).'.format(pid, r.status_code))

if __name__ == '__main__':
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.DEBUG)
    if args.config_file:
      allowed_args = {'ri': 'ri', 'ri-user': 'ri_user', 'ri-pass': 'ri_pass', 'solr': 'solr', 'solr-last-modified-field':'solr_last_modified_field', 'keep-docs': 'keep_docs', 'gsearch': 'gsearch', 'gsearch-user': 'gsearch_user', 'gsearch-pass': 'gsearch_pass', 'query-limit': 'query_limit', 'all': 'all', 'last-n-days': 'last_n_days', 'last-n-seconds': 'last_n_seconds', 'since': 'since', 'verbose': 'verbose', 'quiet': 'quiet'}
      try:
        with open(args.config_file) as data_file:    
          try:
            data = json.load(data_file)
            for key in data:
              if key in allowed_args:
                setattr(args, allowed_args[key], data[key])
          except:
            logging.debug('No JSON to be parsed.')
            exit(-1)
      except IOError:
         logging.debug('The config file does not exist.')
         exit(-1)
    logging.getLogger().setLevel(logging.INFO + (-args.verbose + args.quiet) * 10)

    start = None
    timestamp = 0
    if args.last_n_days:
        timestamp = time.time() - (24 * 3600 * args.last_n_days)
    elif args.last_n_seconds:
        timestamp = time.time() - args.last_n_seconds
    elif args.since:
        timestamp = args.since

    if not args.all:
        # Use "timestamp" to set "start"
        start = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))

    ri = iter(ri_generator(args.ri, args.ri_user, args.ri_pass, start=start, limit=args.query_limit))
    solr = iter(solr_generator(args.solr, args.solr_last_modified_field, start=start, limit=args.query_limit))
    gsearch = gsearch(args.gsearch, args.gsearch_user, args.gsearch_pass, args.keep_docs)

    try:
        ri_result = ri.next()
        solr_result = solr.next()

        while ri_result and solr_result:
            ri_pid, ri_time = ri_result
            solr_pid, solr_time = solr_result

            if ri_time < solr_time:
                logging.debug('RI older, update {0}.'.format(ri_pid))
                gsearch.update_pid(ri_pid)
                ri_result = False
                ri_result = ri.next()
            elif solr_time < ri_time:
                logging.debug('Solr older, update {0}.'.format(solr_pid))
                gsearch.update_pid(solr_pid)
                solr_result = False
                solr_result = solr.next()
            else:
                # Hit stuff with the same time... Start comparing PIDs.
                if ri_pid < solr_pid:
                    logging.debug('RI pid, update {0}.'.format(ri_pid))
                    gsearch.update_pid(ri_pid)
                    ri_result = False
                    ri_result = ri.next()
                elif solr_pid < ri_pid:
                    logging.debug('Solr pid, update {0}.'.format(solr_pid))
                    gsearch.update_pid(solr_pid)
                    solr_result = False
                    solr_result = solr.next()
                else:
                    # Same PID, same time, up-to-date... Skip!
                    logging.debug('Docs appear equal for {0}.'.format(ri_pid))
                    ri_result = False
                    solr_result = False
                    ri_result = ri.next()
                    solr_result = solr.next()
    except StopIteration:
        # Prepend unconsumed items into their respective iterators.
        try:
            if ri_result:
                ri = itertools.chain([ri_result], ri)
        except NameError:
            pass

        try:
            if solr_result:
                solr = itertools.chain([solr_result], solr)
        except NameError:
            pass

    for ri_pid, ri_time in ri:
        # Stuff left over from RI... Reindex.
        logging.debug('RI, leftover: {0}'.format(ri_pid))
        gsearch.update_pid(ri_pid)

    for solr_pid, solr_time in solr:
        # Stuff left over from Solr. Recently indexed and purged, but index
        # failed to update... Should probably delete...  Let's just try
        # reindexing.
        logging.debug('Solr, leftover: {0}'.format(solr_pid))
        if not args.keep_docs:
            gsearch.delete_pid(solr_pid)

    if gsearch.updated:
        exit(1)
    else:
        exit(0)
