import os
import sys
import time
import json
import logging
from datetime import datetime

import boto3
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# SETTINGS
DATA_ROOT = "/tmp/skilzzz/justjoinit"
S3_ROOT = "justjoinit"
S3_BUCKET = "stxnext-sandbox-cp"
# ########

def scrape_justjoinit_offer_list(url: str, scroll_interval: float = 0.2, init_sleep: int = 3, scroll_by: int = 800):
    """This funtion scrape page by loading url and slowly scrolling down. At each scroll html in yielded."""

    logger.info(f"Started Scraping JustJoinIT from url: {url}")
    logger.info(f"Scraping parameters: scroll_interval: {scroll_interval}, scroll_by: {scroll_by}, init_sleep: {init_sleep}")
    
    logger.info("Launching Headless Browser...")
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    logger.info(f"Openning url {url}...")
    driver.get(url)

    logger.info(f"Waiting for {init_sleep} seconds...")
    time.sleep(init_sleep)

    logger.info("Started scrolling")
    while True:
        driver.execute_script(f"""window.scrollBy(0, {scroll_by})""")
        time.sleep(scroll_interval) # seconds

        # Get the current page height
        javascript = """
            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
            return { scrollTop, scrollHeight, clientHeight };
        """
        scroll_props = driver.execute_script(javascript)

        # Access the retrieved scroll properties
        scroll_top = scroll_props['scrollTop']
        scroll_height = scroll_props['scrollHeight']
        client_height = scroll_props['clientHeight']

        # Check if the height has changed
        if scroll_top+client_height >= scroll_height:
            break

        logger.info(f"Current position: {scroll_top+client_height}, Page size: {scroll_height}")

        # Return rendered HTML
        html = driver.page_source

        logger.info(f"Yielded page html ({sys.getsizeof(html)})")
        yield html

    logger.info("Got to the end of page.")
    # Close the ChromeDriver instance

    logger.info("Quit headless browser.")
    driver.quit()


def parse_justjoinit_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    json_data = soup.find_all('script', attrs={'type': "application/json"})[0].text
    queries = json.loads(json_data)['props']['pageProps']['dehydratedState']['queries']

    all_orders = []
    query = queries[0]
    pages = query['state']['data']['pages']
    for page in pages:
        orders = page['data']
        all_orders.extend(orders)


    logger.info(f"Parsed {len(all_orders)} orders.")
    return all_orders


def generate_session_folder() -> str:
    """
    Generate a filepath with timestamp in the format '/year=YYYY/month=MM/day=DD/filename_YYYYMMDDHHMMSS.jsonl'.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The timestamped filepath.
    """
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    year = current_time.strftime("%Y")
    month = current_time.strftime("%m")
    day = current_time.strftime("%d")

    session_folder = f"year={year}/month={month}/day={day}/{timestamp}"
    return session_folder

def extract_justjoinit():
    # S3 Service
    s3 = boto3.client("s3")

    # Extract to html files.
    url = "https://justjoin.it/all-locations/data"

    # JSON
    session_path = generate_session_folder()
    local_json_folder = f"{DATA_ROOT}/json/" + session_path[:-15] # without timestamp folder
    local_html_folder = f"{DATA_ROOT}/html/" + session_path

    session_started_at = datetime.now()
    session_timestamp = session_started_at.strftime("%Y%m%d%H%M%S")

    os.makedirs(local_json_folder, exist_ok=True)
    os.makedirs(local_html_folder, exist_ok=True)

    json_name = f"justjoinit-{session_timestamp}.jsonl" 
    local_json_path = f'{local_json_folder}/{json_name}'
    with open(local_json_path, 'w') as f_json:
        # Start Extracting HTMLs
        for i, html in enumerate(scrape_justjoinit_offer_list(url)):

            # Save HTML file.
            html_name = f"justjoinit-{session_timestamp}-{i}.html"
            local_html_path = f"{local_html_folder}/{html_name}"
            with open(local_html_path, "w") as f_html:
                f_html.write(html)

            s3_path = f"{S3_ROOT}/html/{session_path}/{html_name}"
            s3.upload_file(local_html_path, S3_BUCKET, s3_path)
            logger.info(f"Saved HTML file to S3: {s3_path}")

            # Parse HTML and write to JSON
            try:
                orders = parse_justjoinit_html(html)
            except:
                logger.warning(f"JSON Data not found in html file {s3_path}.")

            metadata = {
                "_scraped_at": session_started_at,
                "_scraped_from": url,
                "_loaded_at": datetime.now(),
                "_source_html": s3_path,
            }

            jsonl_str = '\n'.join([json.dumps({**order, **metadata}, default=str) for order in orders]) + '\n'
            f_json.write(jsonl_str)

    s3_path = f"{S3_ROOT}/json/{session_path[:-15]}/{json_name}"
    s3.upload_file(local_json_path, S3_BUCKET, s3_path)
    logger.info(f"Saved JSON file to S3: {s3_path}")
   
if __name__=="__main__": 
    extract_justjoinit()
    logger.info(f"Success!")
    

