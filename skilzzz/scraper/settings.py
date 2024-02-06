import os

# General
TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
MULTITHREAD_WORKERS = 8
# Selenium
SELENIUM_ADDRESS = os.environ.get('SELENIUM_ADDRESS') or 'localhost:4444'

# AWS S3
S3_BUCKET = "skilzzz"

# Storing settings:
SESSION_ID_REGEX = "sources/.*/year=[0-9]{4}/month=[0-9]{2}/day=[0-9]{2}/ts=[0-9]{14}"