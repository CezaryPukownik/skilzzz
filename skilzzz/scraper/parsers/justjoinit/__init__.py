from scraper.parsers.justjoinit.justjoinit__offers_v1 import parse_offer as v1
from scraper.parsers.justjoinit.justjoinit__offers_v0 import parse_offer as v0

parsers = {
    "v0": v0,
    "v1": v1,
}


