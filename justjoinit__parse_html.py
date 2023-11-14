#%%
from dataclasses import dataclass
from datetime import datetime
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator
from scraper.driver.s3 import S3Driver
from scraper.output import Output, DictOutput
from scraper.partitioner import YMDPartitioner
from scraper.session import Session
from scraper.settings import S3_BUCKET
from scraper.storer import CompactedPartitionedS3DictStorer
from tqdm import tqdm

from bs4 import BeautifulSoup
import re

class JustjoinitJsonlSession(Session):

    def generate_outputs(self, driver, context) -> Generator[Output, None, None]:
        files = driver.list_prefix(prefix=context.prefix)

        futures = []
        with ThreadPoolExecutor() as executor:
            for file in files:
                futures.append(executor.submit(self.generate_output, driver, file))

            for future in tqdm(as_completed(futures), total=len(files)):
                yield future.result()
            

    def generate_output(self, driver, file) -> DictOutput:
        s3_object = driver.get(file)
        html = s3_object.decode('utf-8')
        html_data = self.parse_offer(html)
        key_data = self.parse_key(file)
        return DictOutput(
            content={**key_data, **html_data}
        )
        
    def parse_key(self, key):
        data_from_key = re.findall("ts=([0-9]{12,14})/([0-9]{5})-(.*)\.html", key)
        if data_from_key:
            crawled_at, offer_index, offer_id = data_from_key[0]

        return {
            'listed_at': crawled_at,
            'offer_index': offer_index,
            'offer_id': offer_id
        }


    def parse_offer(self, html: str):
        soup = BeautifulSoup(html, 'lxml')

        job_offer = {}

        # Title
        job_title = soup.select_one('h1').text
        job_offer['title'] = job_title

        # Company
        job_company = soup.select_one('svg[data-testid="ApartmentRoundedIcon"]').parent.text
        job_offer['company'] = job_company

        # Location - City
        location_div = soup.select_one('svg[data-testid="PlaceOutlinedIcon"]').parent
        for span in location_div.find_all('span'):
            span.decompose()

        job_location = location_div.parent.select_one('div', recursive=False).text
        job_offer['city'] = job_location

        # Skills
        skills_h6s = soup.select_one('h6').next_sibling.find_all('h6')
        job_skills = []
        for skill_h6 in skills_h6s:
            skill_name = skill_h6.text
            skill_div = skill_h6.parent
            skill_seniorty = skill_div.select_one('span').text
            job_skills.append(
                {
                    "skill_name": skill_name,
                    "skill_seniorty": skill_seniorty
                }
            )

        job_offer['skills'] = job_skills

        # Salary
        salary_types = []
        salary_section = soup.select_one('h1').next_sibling.next_sibling
        if salary_section:
            salary_divs = salary_section.select_one('div div').find_all('div', recursive=False)
            for salary_div in salary_divs:
                salary_span = salary_div.select_one('span')
                job_salary_from, job_salary_to = [span.text for span in salary_span.find_all('span')]
                salary_type = salary_span.next_sibling.text
                salary_currency = salary_span.find(string=re.compile('[A-Z]{3}'))
                salary_types.append({
                    "from": job_salary_from,
                    "to": job_salary_to,
                    "employment_type": salary_type,
                    "currency": salary_currency
                })

        job_offer['salary_types'] = None or salary_types

        # Additional Info
        info_section = soup.select_one('h1').parent.parent.parent.next_sibling
        info_divs = info_section.find_all('div', recursive=False)
        for info_div in info_divs:
            key, value = info_div.select_one('div').next_sibling.find_all('div')
            snake_case_key = key.text.lower().replace(' ', '_')
            job_offer[snake_case_key]=value.text

        # Description
        description_section = soup.select_one('h1').parent.parent.parent.next_sibling.next_sibling.next_sibling
        job_descripion = description_section.text
        job_offer['description'] = job_descripion

        return job_offer


@dataclass(frozen=True)
class JustjoinitJsonlContext:
    prefix: str

if __name__ == "__main__":

    current_timestamp = datetime.now().strftime("%y%m%d%H%M%S")

    JUSTJOINIT_HTML_LISTING_PATH = 'sources/justjoinit/offerlist/html'
    JUSTJOINIT_HTML_OFFERS_PATH = 'sources/justjoinit/offers/html'
    JUSTJOINIT_JSONL_OFFERS_PATH = 'sources/justjoinit/offers/jsonl'
   
    prefix = "sources/justjoinit/offers/year=2023/month=11/day=14/ts=231114130114"
    origin_session_id = re.findall("ts=([0-9]{12,14})", prefix)[0]

    context = JustjoinitJsonlContext(
        prefix=prefix
    )

    s3_storer = CompactedPartitionedS3DictStorer(
        bucket=S3_BUCKET, 
        prefix=JUSTJOINIT_JSONL_OFFERS_PATH,
        key=f"{origin_session_id}.jsonl", 
        partitioner=YMDPartitioner()
    )

    session = JustjoinitJsonlSession(
        driver=S3Driver('skilzzz'),
        storer=s3_storer
    )

    session.start(context)