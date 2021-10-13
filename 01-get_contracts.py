# -*- coding: utf-8 -*-
"""

Data extracted from:

https://opendata.euskadi.eus/catalogo/-/contrataciones-administrativas-del-2021/

https://opendata.euskadi.eus/katalogoa/-/2021eko-kontratazio-administratiboak/

"""

import requests
import json
import os
import re
from utils import print_progress
import argparse

CONTRACTS_JSON_URL_EU = "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2021/opendata/kontratuak.json"
CONTRACTS_JSON_URL_ES = "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2021/opendata/contratos.json"

LIMIT = 30

REALLY_DOWNLOADED = 0
COUNT = 0


class IDNotFoundError(Exception):
    pass


@print_progress
def get_contracts_from_json(url):
    """ download, cache and extract values from the given JSON url"""
    filename = url.split("/")[-1]

    try:
        with open(f"cache/{filename}", "r") as cache_file:
            return json.load(cache_file)
    except FileNotFoundError:
        sock = requests.get(url)
        data = sock.text

        data_json_txt = data.split("(", 1)[1].strip(");")  # convert to json
        with open(f"cache/{filename}", "w") as cache_file:
            cache_file.write(data_json_txt)

        return json.loads(data_json_txt)


def get_contract_id(contract):
    if "zipFile" in contract:
        zip_file = contract["zipFile"]
        zip_filename = zip_file.split("/")[-1]

        return re.compile("[\d]+").search(zip_filename).group()

    raise IDNotFoundError("Could not find contract ID")


@print_progress
def parse_contract(contract_id, language, contract, update=False):
    try:
        os.makedirs(f"contracts/{contract_id}/{language}")
    except FileExistsError:
        pass
    data_xml_url = contract["dataXML"]
    metadata_xml_url = contract["metadataXML"]

    if update or not os.path.exists(f"contracts/{contract_id}/{language}/data.xml"):
        global REALLY_DOWNLOADED
        REALLY_DOWNLOADED += 1
        with requests.get(data_xml_url) as r:
            if r.ok:
                with open(f"contracts/{contract_id}/{language}/data.xml", "wb") as f:
                    f.write(r.content)

    if update or not os.path.exists(f"contracts/{contract_id}/{language}/metadata.xml"):
        with requests.get(metadata_xml_url) as r:
            if r.ok:
                with open(
                    f"contracts/{contract_id}/{language}/metadata.xml", "wb"
                ) as f:
                    f.write(r.content)

    contract["id"] = contract_id

    if update or not os.path.exists(f"contracts/{contract_id}/{language}/data.json"):
        with open(f"contracts/{contract_id}/{language}/data.json", "w") as f:
            f.write(json.dumps(contract))


def build_contracts_dict(contracts, language):

    return {
        get_contract_id(contract_es): {language: contract_es}
        for contract_es in contracts
    }


def merge_dicts(dict1, dict2):
    for key in dict2:
        if key in dict1:
            dict1[key].update(dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1


def merge_contracts(contracts_es, contracts_eu):
    contracts = merge_dicts(
        build_contracts_dict(contracts_es, "es"),
        build_contracts_dict(contracts_eu, "eu"),
    )
    return contracts


def parse_multilingual_contract(contract_id, contract, update):
    for language, contract_data in contract.items():
        parse_contract(contract_id, language, contract_data, update)


def get_contracts(update):
    contracts_es = get_contracts_from_json(CONTRACTS_JSON_URL_ES)
    contracts_eu = get_contracts_from_json(CONTRACTS_JSON_URL_EU)
    contracts = merge_contracts(contracts_es, contracts_eu)

    global COUNT
    COUNT = 0
    for contract_id, contract in contracts.items():
        parse_multilingual_contract(contract_id, contract, update)
        COUNT += 1
        print(f"Downloaded item count:  {COUNT}")
        if REALLY_DOWNLOADED and REALLY_DOWNLOADED % LIMIT == 1:
            print("Sleeping for 10 seconds")
            import time

            time.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download contracts from the Euskadi Open Data portal"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing contracts",
    )
    myargs = parser.parse_args()

    update = myargs.update

    get_contracts(update)
