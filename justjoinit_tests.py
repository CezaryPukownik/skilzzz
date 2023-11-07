#%%
import time
import string
import random

from selenium import webdriver

def scroll_to_end(url: str, scroll_interval: float):
    """Open a webpage in a ChromeDriver and scroll to the bottom of the page"""
    # Create a ChromeDriver instance
    driver = webdriver.Chrome()

    # Open the URL
    driver.get(url)


    """
        const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
        if (scrollTop + clientHeight >= scrollHeight) {
            resolve();
        } else {
            window.scrollBy(0, increment);
            setTimeout(scrollToBottomLoop, waitTime);
        }
        };
    """

    # init sleep
    time.sleep(5)
    while True:
        driver.execute_script("""window.scrollBy(0, 800)""")
        time.sleep(scroll_interval)

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
        print("scroll_to: ", scroll_top)
        print("scroll_heigh: ", scroll_height)
        print("client_heigh: ", client_height)

        # Check if the height has changed
        if scroll_top+client_height >= scroll_height:
            break


        yield driver.page_source

    # Close the ChromeDriver instance
    driver.quit()

def generate_random_string(length: int) -> str:
    """
    Generate a random string of given length that can be used as a file name.
    Args:
      length: The length of the desired random string.
    Returns:
      A random string of the specified length.
    Raises:
      ValueError: If the length is less than or equal to 0.
    """
    if length <= 0:
        raise ValueError("Length must be greater than 0")
    # Use a combination of lowercase letters, uppercase letters, and digits
    alphanum = string.ascii_letters + string.digits
    # Generate a random string using the specified length
    return ''.join(random.choice(alphanum) for _ in range(length))

# %%
import json


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    try:
        json_data = soup.find_all('script', attrs={'type': "application/json"})[0].text
        queries = json.loads(json_data)['props']['pageProps']['dehydratedState']['queries']

        all_orders = []
        query = queries[0]
        pages = query['state']['data']['pages']
        for page in pages:
            orders = page['data']
            all_orders.extend(orders)

        return all_orders
    except IndexError:
        print("json data not-found")
        return []
# %%
from bs4 import BeautifulSoup
from typing import List

def get_offers_from_html(html_path: str):
    with open(html_path) as f:
        html = f.read()
        return parse_html(html)


# %%

# Extract to html files.
url = "https://justjoin.it/all-locations/data"
session = generate_random_string(10)
for i, html in enumerate(scroll_to_end(url, 1)):
    with open(f"data/justjoinit-{session}-{i}.html", "w") as f:
        f.write(html)

# Read JSON from html files and store in one jsonl file.
import os
data = []
for file in os.listdir("data"):
    file_path = f"data/{file}"
    orders = get_offers_from_html(file_path)
    data.extend(orders)

jsonl_str = '\n'.join([json.dumps(order) for order in data])
print(jsonl_str)
with open('data/justjoinit-wms6l2N10h.jsonl', 'w') as f:
    f.write(jsonl_str)