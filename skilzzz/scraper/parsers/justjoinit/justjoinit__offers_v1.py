import re
from typing import List

from bs4 import BeautifulSoup

from scraper.parsers.exceptions import InvalidHTMLDocument
from scraper.logger import logger

from pydantic import BaseModel, Field, validator

class Skill(BaseModel):
    skill_name: str
    skill_seniorty: str

class SalaryType(BaseModel):
    from_: int = Field(alias="from")
    to: int
    employment_type: str
    currency: str

    @validator("from_", "to", pre=True)
    def parse_salary_amount(cls, value: str) -> int:
        if isinstance(value, str):
            return int(value.replace(" ", ""))
        return value

class JobOffer(BaseModel):
    title: str
    company: str
    city: str
    skills: List[Skill]
    salary_types: List[SalaryType]
    type_of_work: str
    experience: str
    employment_type: str
    operating_mode: str
    description: str

def parse_offer(soup: BeautifulSoup):

    job_offer = {}

    # Title
    if not (job_title := soup.find('h1', class_=True)):
        raise InvalidHTMLDocument("Invalid HTML offer. Title cannot be found.")

    job_offer['title'] = job_title.text.strip()

    # Company
    job_company = soup.find('svg', attrs={'data-testid': 'ApartmentRoundedIcon'}).parent.text
    job_offer['company'] = job_company.strip()

    # Location - City
    job_location = soup.find('svg', attrs={'data-testid': 'PlaceOutlinedIcon'}).parent.text
    job_offer['city'] = job_location.strip()

    # Skills
    tech_stack_title = soup.find(lambda tag: tag.text.strip().lower() == "tech stack") 
    skills_section = tech_stack_title.parent

    if skills_section == None:
        raise InvalidHTMLDocument("Invalid HTML offer. Skills (Tech Stack) section cannot be found.")

    job_skills = []
    for skill_h6 in skills_section.select_one('ul').find_all('h6'):
        skill_name = skill_h6.text
        skill_div = skill_h6.parent
        skill_seniorty = skill_div.select_one('span').text
        job_skills.append(
            {
                "skill_name": skill_name.strip(),
                "skill_seniorty": skill_seniorty.strip()
            }
        )

    job_offer['skills'] = job_skills

    # Salary
    salary_types = []
    salary_section = job_title.next_sibling.next_sibling
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
    info_section = job_title.parent.parent.parent.find_next_sibling('div')
    info_divs = info_section.find_all('div', recursive=False)
    for info_div in info_divs:
        key, value = info_div.find('div').find_next_sibling('div').find_all('div')
        snake_case_key = key.text.lower().strip().replace(' ', '_')
        job_offer[snake_case_key]=value.text.strip()

    # Description
    job_descripion_title = soup.find(lambda tag: tag.name.startswith('h') and tag.text.strip().lower() == "job description")
    description_section = job_descripion_title.parent.find_next_sibling('div')
    job_descripion = description_section.text
    job_offer['description'] = job_descripion

    # Schema Validation
    JobOffer.model_rebuild()
    job_offer = JobOffer.model_validate(job_offer)
    return job_offer.model_dump(by_alias=True)
