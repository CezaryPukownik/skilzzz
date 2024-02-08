import re

from bs4 import BeautifulSoup

from scraper.parsers.exceptions import InvalidHTMLDocument
from scraper.logger import logger



def parse_offer(soup: BeautifulSoup):

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

