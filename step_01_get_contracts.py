# -*- coding: utf-8 -*-
"""

Data extracted from:

https://opendata.euskadi.eus/catalogo/-/contrataciones-administrativas-del-2021/

https://opendata.euskadi.eus/katalogoa/-/2021eko-kontratazio-administratiboak/

"""

import argparse
import json
import os
import re

import requests

from step_00_cache_contracts_files import CONTRACT_URLS
from utils import print_progress

LIMIT = 30

REALLY_DOWNLOADED = 0
COUNT = 0


def merge_dicts(dict1, dict2):
    for key in dict2:
        if key in dict1:
            dict1[key].update(dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1


class IDNotFoundError(Exception):
    pass


class ContractDownloader:
    def __init__(self, year, update):
        self.year = year
        self.update = update

    def get_contracts_from_json(self, language):
        """ download, cache and extract values from the given JSON url"""
        url = CONTRACT_URLS[self.year][language]
        filename = url.split("/")[-1]

        os.makedirs(f"cache/{self.year}/{language}", exist_ok=True)

        try:
            with open(f"cache/{self.year}/{language}/{filename}", "r") as cache_file:
                return json.load(cache_file)
        except FileNotFoundError:
            print(f"Downloading {url}")
            sock = requests.get(url)
            data = sock.text

            data_json_txt = data.split("(", 1)[1].strip(");")  # convert to json
            with open(f"cache/{self.year}/{language}/{filename}", "w") as cache_file:
                cache_file.write(data_json_txt)

            print(f"File created cache/{self.year}/{language}/{filename}")
            return json.loads(data_json_txt)

    def get_contract_id(self, contract):
        if "zipFile" in contract:
            zip_file = contract["zipFile"]
            zip_filename = zip_file.split("/")[-1]

            return re.compile("[\d]+").search(zip_filename).group()

        import uuid

        return uuid.uuid4().hex
        raise IDNotFoundError("Could not find contract ID")

    def parse_contract(self, contract_id, language, contract):
        if "dataXML" in contract and "metadataXML" in contract:
            contract_base_url = f"contracts/{self.year}/{contract_id}/{language}"
            os.makedirs(contract_base_url, exist_ok=True)
            data_xml_url = contract["dataXML"]
            metadata_xml_url = contract["metadataXML"]

            if self.update or not os.path.exists(f"{contract_base_url}/data.xml"):
                global REALLY_DOWNLOADED
                REALLY_DOWNLOADED += 1
                with requests.get(data_xml_url) as r:
                    if r.ok:
                        with open(f"{contract_base_url}/data.xml", "wb") as f:
                            f.write(r.content)

            if self.update or not os.path.exists(f"{contract_base_url}/metadata.xml"):
                with requests.get(metadata_xml_url) as r:
                    if r.ok:
                        with open(f"{contract_base_url}/metadata.xml", "wb") as f:
                            f.write(r.content)

            contract["id"] = contract_id

            if update or not os.path.exists(f"{contract_base_url}/data.json"):
                with open(f"{contract_base_url}/data.json", "w") as f:
                    f.write(json.dumps(contract))
        else:
            print(f"{contract_id} is not correct")

    def build_contracts_dict(self, contracts, language):

        return {
            self.get_contract_id(contract_es): {language: contract_es}
            for contract_es in contracts
        }

    def merge_contracts(self, contracts_es, contracts_eu):
        contracts = merge_dicts(
            self.build_contracts_dict(contracts_es, "es"),
            self.build_contracts_dict(contracts_eu, "eu"),
        )
        return contracts

    def parse_multilingual_contract(self, contract_id, contract):
        for language, contract_data in contract.items():
            self.parse_contract(contract_id, language, contract_data)

    def get_contracts(self):
        contracts_es = self.get_contracts_from_json("es")
        contracts_eu = self.get_contracts_from_json("eu")
        contracts = self.merge_contracts(contracts_es, contracts_eu)

        global COUNT
        COUNT = 0
        for contract_id, contract in contracts.items():
            self.parse_multilingual_contract(contract_id, contract)
            COUNT += 1
            print(f"Downloaded item count:  {COUNT}")
            if REALLY_DOWNLOADED and REALLY_DOWNLOADED % LIMIT == 0:
                print("Sleeping for 10 seconds")
                import time

                time.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download contracts from the Euskadi Open Data portal"
    )
    parser.add_argument("year", help="Enter the year to download")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing contracts",
    )
    myargs = parser.parse_args()

    year = myargs.year
    update = myargs.update

    if year not in CONTRACT_URLS.keys():
        print(
            "Year must be one of the followings: {}".format(
                ",".join(CONTRACT_URLS.keys())
            )
        )
    else:
        cd = ContractDownloader(year, update)
        cd.get_contracts()
