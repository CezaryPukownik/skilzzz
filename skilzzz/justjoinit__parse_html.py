import json
import click

from dataclasses import dataclass
from datetime import datetime
from typing import Generator
from scraper.producer.storage import StorageProducer
from scraper.output import Output, DictOutput
from scraper.session import Session, SessionMetadata
from scraper.settings import TIMESTAMP_FORMAT
from scraper.stepfunctions import stepfunctions_callback_handler
from scraper.storer import AppendStorer
from scraper.logger import logger
from parsers.exceptions import InvalidHTMLDocument

from bs4 import BeautifulSoup
import re

import traceback


class JustjoinitStorer(AppendStorer):
    """
    In this case we dont want to close file after ending session
    because item will be yielded by child session. Files will be 
    manually closed by main session.
    """
    def on_session_end(self):
        pass


@dataclass(frozen=True)
class JustjoinitOffersFanoutSettings:
    pattern: str

@dataclass(frozen=True)
class JustjoinitOfferParserSettings:
    file: str

class JustjoinitOffersFanout(Session):
    """
    CAUTION: Always run at minimum whole session run! 
    Running single html will most likely result in missing data.
    """

    def process(self) -> Generator[Output, None, None]:
        files = self.producer.glob(pattern=self.settings.pattern)
        for file in files:
            logger.info(f"Created parsing session for file {file}")
            yield JustjoinintOfferParser(
                name=self.name,
                collection=self.collection,
                producer=self.producer,
                storer=self.storer,
                settings=JustjoinitOfferParserSettings(
                    file=file
                )
            )
        else:
            logger.info(f"No files is given pattern {self.settings.pattern}")

    def after_process(self):
        # Mannualy closed all opened files after.
        opened = [file for file, _ in self.storer.storage.opened.items()]
        for file in opened:
            self.storer.storage.close(file)

class JustjoinintOfferParser(Session):
                
    def process(self) -> Generator[Output, None, None]:
        try:
            # Getting ts from files session.
            if not (match := re.findall("ts=([0-9]{14})/([0-9]{5})-(.*).html", self.settings.file)):
                raise ValueError("Cannot parse ts from filepath corrently")

            # Act as continuation of file processing session
            session_ts, offer_index, offer_id = match[0]
            session_dt = datetime.strptime(session_ts, TIMESTAMP_FORMAT)
            self.metadata = SessionMetadata(
                session_dt = session_dt,
                session_ts = session_ts
            ) 
            
            # Load html from filesystem
            file_content = self.producer.get(self.settings.file)
            logger.info(f"Loaded {self.settings.file} from {self.producer.__class__.__name__}")

            soup = BeautifulSoup(file_content, "lxml")
            parsed_offer = self.parse_offer(soup)
            yield DictOutput(
                key=f"justjoinit-offers-{session_ts}.jsonl",
                content={
                    "listed_at": session_ts, 
                    "offer_index": offer_index,
                    "offer_id": offer_id,
                    **parsed_offer
                }
            )
        except InvalidHTMLDocument as e:
            logger.error(f"Cannot parse file {self.settings.file} due to recognized invalid html. {e}")
        except Exception as e:
            traceback_str = "".join(traceback.format_tb(e.__traceback__))
            logger.critical(f"Cannot parse file {self.settings.file}. Unhandled exception:\n{e}\n{traceback_str}")
                    
        
    def parse_offer(self, soup: BeautifulSoup):

        job_offer = {}

        # Title
        job_title = soup.select_one('h1')
        if job_title == None:
            raise InvalidHTMLDocument("Invalid HTML offer. Title cannot be found.")

        job_offer['title'] = job_title.text

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
        sections = soup.select_one('h1').parent.parent.parent.parent.find_all('div', recursive=False)
        skills_section = None
        for section in sections:
            has_h6 = section.select_one('h6')
            if has_h6 and has_h6.text.lower() == 'tech stack':
                skills_section = section
                break

        if skills_section == None:
            raise InvalidHTMLDocument("Invalid HTML offer. Skills (Tech Stack) section cannot be found.")

        job_skills = []
        for skill_h6 in skills_section.select_one('ul').find_all('h6'):
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
                
                salaries = [span.text for span in salary_span.find_all('span')]
                match len(salaries):
                    case 1: job_salary_from = job_salary_to = salaries[0]
                    case 2: job_salary_from, job_salary_to = salaries 
                    case _: logger.warning("Didn't parse salaries! Investigate whats wrong.")

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


@click.command()
@click.option("--pattern")
@click.option("--read", default='fs')
@click.option("--write", default='fs')
@stepfunctions_callback_handler
def main(pattern, read, write):
    assets = JustjoinitOffersFanout(
        name="justjoinit",
        collection="offers",
        producer=StorageProducer(storage=read),
        storer=JustjoinitStorer(storage=write),
        settings=JustjoinitOffersFanoutSettings(
            pattern=pattern
        )
    ).start()

    logger.info("Session output:\n" + json.dumps(assets, indent=4))
    return assets

if __name__=="__main__":
    main()