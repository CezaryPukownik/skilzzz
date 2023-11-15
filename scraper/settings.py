import os

SELENIUM_ADDRESS = os.environ['SELENIUM_ADDRESS'] or 'localhost:4444'
JUSTJOINIT_HTML_LISTING_PATH = 'sources/justjoinit/offerlist/html'
JUSTJOINIT_HTML_OFFERS_PATH = 'sources/justjoinit/offers/html'
JUSTJOINIT_JSONL_OFFERS_PATH = 'sources/justjoinit/offers/jsonl'
S3_BUCKET = "skilzzz"


TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"