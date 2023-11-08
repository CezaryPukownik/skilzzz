import os
import time
import json
from datetime import datetime

from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# SETTINGS
DATA_ROOT = "data"
# ########

def scrape_justjoinit_offer_list(url: str, scroll_interval: float = 0.2, init_sleep: int = 3, scroll_by: int = 800):
    """This funtion scrape page by loading url and slowly scrolling down. At each scroll html in yielded."""
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    time.sleep(init_sleep)
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

        # Return rendered HTML
        yield driver.page_source

    # Close the ChromeDriver instance
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

    return all_orders


def generate_session_folder(root_folder: str) -> str:
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

    session_folder = f"{root_folder}/year={year}/month={month}/day={day}/{timestamp}"
    return session_folder

def extract_justjoinit():
    # Extract to html files.
    url = "https://justjoin.it/all-locations/data"

    # JSON
    json_folder = generate_session_folder(f"{DATA_ROOT}/json")[:-14]
    html_folder = generate_session_folder(f"{DATA_ROOT}/html")
    session_started_at = datetime.now()
    session_timestamp = session_started_at.strftime("%Y%m%d%H%M%S")

    os.makedirs(json_folder, exist_ok=True)
    os.makedirs(html_folder, exist_ok=True)

    with open(f'{json_folder}/justjoinit-{session_timestamp}.jsonl', 'w') as f_json:

        # Start Extracting HTMLs
        for i, html in tqdm(enumerate(scrape_justjoinit_offer_list(url))):

            # Save HTML file.
            html_name = f"justjoinit-{session_timestamp}-{i}.html"
            html_path = f"{html_folder}/{html_name}"
            with open(html_path, "w") as f_html:
                f_html.write(html)

            # Parse HTML and write to JSON
            try:
                orders = parse_justjoinit_html(html)
            except:
                print(f"{datetime.now()} [WARNING] JSON Data not found in html file {html_path}.")

            metadata = {
                "_scraped_at": session_started_at,
                "_scraped_from": url,
                "_loaded_at": datetime.now(),
                "_source_html": html_path,
            }
            jsonl_str = '\n'.join([json.dumps({**order, **metadata}, default=str) for order in orders]) + '\n'
            f_json.write(jsonl_str)
   
if __name__=="__main__": 
    extract_justjoinit()
    

