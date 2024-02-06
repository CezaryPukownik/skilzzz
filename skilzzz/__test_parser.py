
from bs4 import BeautifulSoup
import click
from scraper.parsers.justjoinit.justjoinit__offers_init import parse_offer
from scraper.producer.storage import StorageProducer


@click.command()
@click.option("--html")
@click.option("--storage")
def main(html, storage):

    producer = StorageProducer(storage=storage)
    content = producer.get(html)
    soup = BeautifulSoup(content, 'lxml')
    output = parse_offer(soup)
    print(output)



if __name__=="__main__":
   main() 