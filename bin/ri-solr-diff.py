#!/usr/sbin/env python

import dateutil.parser
import time
import requests
import argparse
import logging
import json as asdf
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%s')

parser = argparse.ArgumentParser(description='Identify and resolve differences between a Fedora Resource and Solr index.')
# Connection arguments
parser.add_argument('--ri', default="http://localhost:8080/fedora/risearch", help='URL of the resource index at the host.')
parser.add_argument('--ri-user', default='fedoraAdmin', help='Username to communicate with resource index, if necessary.')
parser.add_argument('--ri-pass', default='islandora', help='Password to communicate with resource index, if necessary.')
parser.add_argument('--solr', default="http://localhost:8080/solr", help='Hostname/IP of the Solr index.')
parser.add_argument('--solr-last-modified-field', dest='solr_field', default='fgs_lastModifiedDate_dt', help='The Solr field storing the last modified date of each object.')
parser.add_argument('--gsearch', default="http://localhost:8080/fedoragsearch/rest", help="Hostname/IP of GSearch")
parser.add_argument('--gsearch-user', default='fedoraAdmin', help='Username to communicate with GSearch servelet, if necessary.')
parser.add_argument('--gsearch-pass', default='islandora', help='Password to communicate with GSearch servelet, if necessary.')
parser.add_argument('--query-limit', default=10000, type=int, help='The number of results which will be fetched from the RI and Solr at a time.')

# Application switches
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--all', help='Compare all objects.', action='store_true')
group.add_argument('--last-n-days', type=int, help='Compare objects modified in the last n days.')
group.add_argument('--last-n-seconds', type=int, help='Compare objects modified in the last n seconds.')
group.add_argument('--since', type=int, help='Compare objects modified since the given Unix timestamp.')

class ri_generator:
    def __init__(self, url, user=None, password=None, start=None, limit=10000):
        self.url = url
        self.user = user
        self.password = password
        self.start = start
        self.limit = limit

    def __iter__(self):
        replacements = {
          'filter': ''
        }
        if self.start is not None:
            replacements['filter'] = 'FILTER(?timestamp >= "%s"^^<http://www.w3.org/2001/XMLSchema#dateTime>)' % (self.start)

        query = '''
SELECT ?obj ?timestamp
FROM <#ri>
WHERE {
  ?obj <fedora-model:hasModel> <info:fedora/fedora-system:FedoraObject-3.0> ;
       <fedora-view:lastModifiedDate> ?timestamp .
  %(filter)s
}
ORDER BY ?timestamp ?obj
'''
        data = {
            'type': 'tuples',
            'format': 'json',
            'lang': 'sparql',
            'query': query % replacements
        }
        r = requests.post(self.url, auth=(self.user, self.password), data=data)

        while r.status_code == requests.codes.ok:
            print(r.content)
            json = r.json()

            if len(json['results']) == 0:
              break

            for result in json['results']:
                yield (result['obj'].split('info:fedora/')[1], result['timestamp'], dateutil.parser.parse(result['timestamp']))
            self.start = json['results'][-1]['timestamp']

            replacements['filter'] = 'FILTER(?timestamp > "%s"^^<http://www.w3.org/2001/XMLSchema#dateTime>)' % (self.start)
            data['query'] = query % replacements
            r = requests.post(self.url, auth=(self.user, self.password), data=data)

class solr_generator:
    def __init__(self, url, field, start=None, limit=10000):
        self.url = url
        self.field = field
        self.start = start
        self.limit = 10000

    def __iter__(self):
        params = {
          'sort': '%s asc PID asc' % self.field,
          'wt': 'json',
          'fl': 'PID %s' % self.field,
          'rows': self.limit
        }
        if self.start is not None:
            params['fq'] = "%s:{%s TO *}" % (self.field, self.start)

        r = requests.post(self.url, data=params)

        while r.status_code == requests.codes.ok:
            json = r.json()

            if json['response']['numFound'] == 0:
              break

            for result in json['response']['docs']:
                yield (result['PID'], result[self.field], dateutil.parser.parse(result[self.field]))

            self.start = json['response']['docs'][-1][self.field]

            params['fq'] = "%s:{%s TO *}" % (self.field, self.start)
            r = requests.post(self.url, data=params)

class gsearch:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def update_pid(self, pid):
        data = {
          'operation': 'updateIndex',
          'action': 'fromPid',
          'value': pid
        }
        logging.debug('Attempting to update %s...' % pid)
        r = request.post(self.url, auth=(self.user, self.password), data=data)
        if r.status_code == requests.code.ok:
            logging.debug('Updated %s' % pid)
            logging.info(pid)
        else:
            logging.debug('Failed to update %s?' % pid)

if __name__ == '__main__':
    args = parser.parse_args()

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
    solr = iter(solr_generator(args.solr, args.solr_field, start=start, limit=args.query_limit))
    gsearch = gsearch(args.gsearch, args.gsearch_user, args.gsearch_pass)

    ri_result = ri.next()
    solr_result = solr.next()

    while ri_result and solr_result:
        ri_pid, ri_timestring, ri_time = ri_result
        solr_pid, solr_timestring, solr_time = solr_result

        if ri_time < solr_time:
            gsearch.update_pid(ri_pid)
            ri_result = ri.next()
        elif solr_time < ri_time:
            gsearch.update_pid(solr_pid)
            solr_result = solr.next()
        else:
            # Hit stuff with the same time... Start comparing PIDs.
            if ri_pid < solr_pid:
                gsearch.update_pid(ri_pid)
                ri_result = ri.next()
            elif solr_pid < ri_pid:
                gsearch.update_pid(solr_pid)
                solr_result = solr.next()
            else:
              # Same PID, same time, up-to-date... Skip!
                ri_result = ri.next()
                solr_result = solr.next()

    while ri_result:
        #Stuff left over from RI... Reindex.
        ri_pid, ri_timestring, ri_time = ri_result
        gsearch.update_pid(ri_pid)
        ri_result = ri.next()

    while solr_result:
        # Stuff left over from Solr. Recently indexed and purged, but index
        # failed to update... Should probably delete...  Let's just try
        # reindexing.
        solr_pid, solr_timestring, solr_time = solr_result
        gsearch.update_pid(solr_pid)
        solr_result = solr.next()
