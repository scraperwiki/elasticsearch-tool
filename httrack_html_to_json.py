#!/usr/bin/env python
# encoding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)
from collections import OrderedDict
from datetime import datetime

import codecs
import json
import logging
import re
import sys

import lxml.html
import lxml.html.clean


def read_file(input_filename):
    """ Return content of file. """
    with codecs.open(input_filename, 'r', encoding='utf-8') as f:
        return f.read()


def clean_html(element):
    """
    Take element and return a cleaned element (along with children).
    
    Removes styles, scripts, comments, links etc. from element
    and its child elements.

    See http://lxml.de/3.4/api/lxml.html.clean.Cleaner-class.html
    """
    cleaner = lxml.html.clean.Cleaner(style=True)
    cleaned_html = cleaner.clean_html(element)
    for el in cleaned_html.xpath("*//p|//br"):
        el.tail = "\n" + el.tail if el.tail else "\n"
    return cleaned_html


def write_output(output_filename, content):
    """ Write content to output file. """
    with codecs.open(output_filename, 'w', encoding='utf-8') as f:
        f.write(content)


def get_title_text(root):
    """ Returns title text from root HTML element. """
    title, = root.xpath('//title')
    return title.text_content()


def get_httrack_info_comment(root):
    """ Returns comment text containing date, URL. """
    comments = root.xpath('//comment()[contains(.,"HTTrack Website Copier")]')
    # TODO: Weird. Some pages have both comments in but this assertion fails.
    # Don't know why so commenting out for now.
    #try:
    #    assert len(comments) == 2
    # Take earliest comment for date and time as started scraping then. 
    #except AssertionError:
    #    logging.info(comments)
    #    logging.info(len(comments))
    return comments[0]


def extract_url_and_datetime_from_httrack_comment(comment):
    """
    Take string HTTrack comment; return url, datetime as strings.
    """
    data_regex = ("<!-- Mirrored from (?P<url>.*) by HTTrack Website Copier/3.x"
                  " \[XR&CO'2014], (?P<datetime>.*) -->")
    results = re.match(data_regex, comment)
    # Add http missing from HTTrack URL; potential issues with https links?
    url = 'http://' + results.group('url') 
    return url, results.group('datetime')


def get_date_from_httrack_comment_datetime(datetime_string):
    """
    Take string datetime from HTTrack comment; return date as string.
    
    >>> get_date_from_httrack_comment_datetime("Fri, 10 Apr 2015 11:18:21 GMT")
    '2015-04-10'
    """
    # TODO: Check whether httrack date/time numbers are zero padded.
    # Assuming yes for now.
    # TODO: Does GMT vary depending on locale? Assuming no for now.
    datetime_object = datetime.strptime(datetime_string, '%a, %d %b %Y %H:%M:%S GMT')
    return datetime_object.date().isoformat()


def make_json(title, url, date, body):
    """ Take metadata and body as strings; return JSON document. """
    document = OrderedDict([
        ('title', title),
        ('url', url),
        ('scrape_date', date),
        ('body', body.text_content())])
    return json.dumps(document, indent=2)


def main():
    """ Read HTML file and output cleaned text from it. """
    logging.basicConfig(level=logging.INFO)
    logging.info("Processing: {}".format(sys.argv[1]))
    content = read_file(sys.argv[1])
    new_content = re.sub(r'(\r\n|\n|\r)+', ' ', content)    
    root = lxml.html.fromstring(new_content)
    
    # TODO: Tidy. And consider making a document class. 
    title = get_title_text(root)
    httrack_comment = unicode(get_httrack_info_comment(root))
    url, datetime_string = extract_url_and_datetime_from_httrack_comment(
                               httrack_comment)
    date = get_date_from_httrack_comment_datetime(datetime_string)
    body, = root.xpath('//body')
    cleaned_body = clean_html(body)
 
    doc_json = make_json(title, url, date, cleaned_body)
    write_output(sys.argv[1] + '.json', doc_json)


if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    main()
