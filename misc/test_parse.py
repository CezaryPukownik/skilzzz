#%%
from bs4 import BeautifulSoup

with open("/home/cezary/STXNext-Demos/skilzzz/data/justjoinit/offerlist/year=2023/month=11/day=14/231114090855-00001.html") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
# %%
offers = soup.select("[data-index]")
offer = offers[0]
offer
# %%
offer.select_one('a').get('href')
# %%
from bs4 import BeautifulSoup
htmlpath = "data/justjoinit/offerlist/year=2023/month=11/day=14/ts=231114110204/231114110204-00003.html"
for file in os.listdir()
with open(htmlpath) as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
soup
# %%