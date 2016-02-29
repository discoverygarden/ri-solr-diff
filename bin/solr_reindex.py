#!/usr/bin/env python

import argparse
import requests
import sys
import logging
import csv
from ri_solr_diff import gsearch

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%s', level=logging.INFO)

parser = argparse.ArgumentParser(
    description='Trigger a Solr re-index for a list of PIDs parsed from CSV.',
    epilog='Exit code will be "1" if re-index was succcesful, "0" otherwise.'
)

parser.add_argument('--gsearch', default="http://localhost:8080/fedoragsearch/rest", help="URL of the GSearch end-point. (default: %(default)s)")
parser.add_argument('--gsearch-user', default='fedoraAdmin', help='Username to communicate with GSearch servelet. (default: %(default)s)')
parser.add_argument('--gsearch-pass', default='islandora', help='Password to communicate with GSearch servelet. (default: %(default)s)')

if __name__ == '__main__':
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug(args)    
    gsearch = gsearch(args.gsearch, args.gsearch_user, args.gsearch_pass, False)
    pids = csv.reader(sys.stdin)
    for row in pids:
       pid = row[0]
       if ':' in pid:
         gsearch.update_pid(pid)
       else:
         logging.debug('Parsed pid {0} is not a valid pid.'.format(pid))
    if gsearch.updated:
        exit(1)
    else:
        exit(0)
 
