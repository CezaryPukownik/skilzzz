"""
For Interactive Session

ipython -i skilzzz/__test_parser.py -- \
    --html "sources/justjoinit/offers/html/year=2024/month=01/day=04/ts=20240104021409/00009-itds-devops-database-specialist-warsaw-333962.html" \
    --storage s3 \
    --open-browser

    
For Testing Parser
"""

import argparse
import json
from bs4 import BeautifulSoup
from scraper.producer.storage import StorageProducer
from scraper.parsers.justjoinit import parsers
from scraper.logger import logger

import tempfile
import webbrowser

from scraper.parsers.exceptions import InvalidHTMLDocument

test_htmls = [
    "sources/justjoinit/offers/html/year=2024/month=02/day=06/ts=20240206154653/00003-profiauto-software-house-analityk-biznesowo-systemowy-it-chorzow.html",
    "sources/justjoinit/offers/html/year=2023/month=11/day=14/ts=20231114130114/00013-xtb-data-scientist-poznan.html",
    "sources/justjoinit/offers/html/year=2024/month=02/day=08/ts=20240208021409/00392-state-street-cloud-incident-responder-avp.html" # invalid html
]


def init_script():
    global soup
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=str, required=True)
    parser.add_argument('--storage', type=str, required=True)
    parser.add_argument('--open-browser', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    producer = StorageProducer(storage=args.storage)
    content = producer.get(args.html)
    soup = BeautifulSoup(content, 'lxml')

    if args.open_browser:
        open_soup(content)

    try:
        result = parsers['v1'](soup)
        logger.info(json.dumps(result, indent=4))
    except InvalidHTMLDocument as e:
        logger.error("Error while parsing")
        logger.error(str(e))


def open_soup(content: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

    # Open the temporary file in the default web browser
    webbrowser.open(f"file://{temp_file_path}")

init_script() 