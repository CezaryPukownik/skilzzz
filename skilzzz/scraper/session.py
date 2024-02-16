from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import json
import re
from typing import Dict, Generator, Set, List
from itertools import takewhile

from functools import partial

from scraper.logger import logger
from scraper.output import Output
from scraper.settings import MULTITHREAD_WORKERS, SESSION_ID_REGEX, TIMESTAMP_FORMAT


@dataclass(frozen=True)
class SessionMetadata:
    session_dt: datetime
    session_ts: datetime

class Session(ABC):
    def __init__(self, name: str, collection: str, producer, storer, settings, is_test=False):
        self.name = name
        self.collection = collection
        self.producer = producer
        self.storer = storer
        self.settings = settings
        self.is_test = is_test
        self.metadata = self.create_metadata()

    def start(self) -> None:
        try:
            with ThreadPoolExecutor(max_workers=MULTITHREAD_WORKERS) as executor:
                # signal can be Output or Session
                futures = []
                assets = defaultdict(set)
                for i, signal in enumerate(self.process()):

                    # Test run, only first 10 outputs.
                    if i >= 10 and self.is_test:
                        logger.info("Ended session after 5 outputs.")
                        break
                    
                    # Store if session yielded Output
                    if isinstance(signal, Output):
                        output = signal

                        logger.info(f"Procesing output: {output}")
                        output.session = self
                        asset_path = self.storer.store(output=output)
                        assets[self.collection].add(asset_path)
                        
                        self.storer.on_output_stored()
                        self.producer.on_output_stored()

                    # Run session, if new session was yielded
                    if isinstance(signal, Session):
                        new_session = signal
                        # Inherit parent session metadata
                        signal.metadata = self.metadata
                        future = executor.submit(new_session.start)
                        futures.append(future)

                # Collect all results from child processes
                results = [future.result() for future in futures]
                combined_dict = defaultdict(set)
                for d in results + [assets]:
                    for key, value in d.items():
                        combined_dict[key].update(value)

                # The result is a dictionary with combined lists
                assets = dict(combined_dict)

            self.after_process() 

            session_folders = self.get_session_folders_from_assets(assets)
            return session_folders

        except Exception as e:
            self.storer.on_session_fail()
            self.producer.on_session_fail()
            logger.error(str(e))
            raise e

        finally:
            self.storer.on_session_end()
            self.producer.on_session_end()

    def create_metadata(self) -> SessionMetadata:
        session_dt = datetime.now()
        session_ts = session_dt.strftime(TIMESTAMP_FORMAT)

        return SessionMetadata(session_dt, session_ts)

    def get_session_folders_from_assets(self, assets: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        session_folders = {}
        for collection, paths in assets.items():
            # reduce granularity from asset to session folder
            collection_folders = { re.findall(SESSION_ID_REGEX, path)[0] for path in paths }
            session_folders[collection] = list(collection_folders)

        return session_folders
            

    @abstractmethod
    def process(self) -> Generator[Output, None, None]:
        ...

    def after_process(self):
        ...