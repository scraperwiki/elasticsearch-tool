#!/usr/bin/env python

from __future__ import print_function
import json
import os
import sys

import requests

import scraperwiki

def main(argv=None):
    if argv is None:
        argv = sys.argv
    arg = argv[1:]

    if len(arg) > 0:
        # Developers can supply URL as an argument...
        url = arg[0]
    else:
        # ... but normally the URL comes from the allSettings.json file
        with open(os.path.expanduser("~/allSettings.json")) as settings:
            keywords = json.load(settings)['input']

    return store_search(keywords)


def store_search(keywords):
    """
    Store results of search to .
    """
    base_url = "http://localhost:59742/blog/post/_search"
    params = {'q': 'body:' + keywords, 'pretty': 'true'}
    response = requests.get(base_url, params=params)
    j = response.json()
    scraperwiki.sql.execute('DROP TABLE IF EXISTS results')

    hits = j['hits']['hits']
    
    results = []
    for hit in hits:	        
        doc = hit['_source']['body'] 
   	score = hit['_score']
 	doc_id = hit['_id']
	results.append(dict(doc=doc, score=score, doc_id=doc_id))
    
    scraperwiki.sql.save(unique_keys=['doc_id'], data=results, table_name='results')
    
if __name__ == '__main__':
    main()
