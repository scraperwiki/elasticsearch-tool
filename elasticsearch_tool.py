#!/usr/bin/env python

from __future__ import print_function
from collections import OrderedDict
import json
import os
import sys

import addict
from elasticsearch import Elasticsearch

import scraperwiki

def main(argv=None):
    if argv is None:
        argv = sys.argv
    arg = argv[1:]

    if len(arg) > 0:
        # Developers can supply URL as an argument...
        keywords = arg[0]
    else:
        # ... but normally the URL comes from the allSettings.json file
        with open(os.path.expanduser("~/allSettings.json")) as settings:
            keywords = json.load(settings)['input']

    return run_search(keywords)


def create_search_body(keywords):
    """ Take keywords; return addict containing ElasticSearch body. """
    body = addict.Dict()
    body.query.match.body = keywords
    body.highlight.fields.body = {}
    return body


def save_results_to_sqlite(result):
    """ Take ElasticSearch result and store in SQLite. """
    hits = result['hits']['hits']
    results = []
    
    for hit in hits:	        
        result = OrderedDict()
        result['doc_id'] = hit['_id']
        result['title'] = hit['_source']['title']
        result['url'] = hit['_source']['url']
        result['score'] = hit['_score']
        result['doc_full_text'] = hit['_source']['body']
        result['highlight'] = '...'.join(hit['highlight']['body'])
        results.append(result)
    scraperwiki.sql.save(unique_keys=['doc_id'],
                         data=results,
                         table_name='results')

 
def run_search(keywords):
    """ Store results from ElasticSearch keyword search to SQLite. """
    body = create_search_body(keywords)   
    es = Elasticsearch([{'host': 'localhost', 'port': 59742}])
    result = es.search(index='documents', doc_type='document', body=body)
    scraperwiki.sql.execute('DROP TABLE IF EXISTS results')
    save_results_to_sqlite(result)

 
if __name__ == '__main__':
    main()
