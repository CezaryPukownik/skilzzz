#%%
from pathlib import Path
import os

from bs4 import BeautifulSoup
import json

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




#__next > div.MuiBox-root.css-1v89lmg > div.css-c4vap3 > div > div.MuiBox-root.css-1fmajlu > div > div > div:nth-child(3) > div > div:nth-child(2)

#%%


len(offers)
# %%
import re

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    offers = soup.select("[data-index]")
    result = []
    for offer in offers:
        offer_index = offer.get('data-index')
        offer_title = offer.find('h2').text
        offer_company = offer.find_all('svg', {'data-testid': "ApartmentRoundedIcon"})[0].parent.select('span')[0].text
        offer_link = offer.find('a').get('href')
        salary = offer.find('h2').parent.find('span').text
        skills_divs = offer.find_all('div', {'class': re.compile(r'skill-tag-\d*')})
        skills = [skill.text for skill in skills_divs]
        result.append(
            (
                offer_index,
                offer_title,
                offer_company,
                offer_link,
                salary,
                skills
            )
        )

    return result

# for row in result:
#     print(row)


folder = Path("data")
session_rows = []
for file in os.listdir(folder):
    with open(f"data/{file}") as f:
        html = f.read()

    rows = parse_html(html)
    session_rows.extend(rows)

#%%
for row in sorted(session_rows, key=lambda row: int(row[0])):
    print(row)
# %%
# %%
len(set([int(x[0]) for x in session_rows]))
# %%
