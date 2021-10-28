# -*- coding: utf-8 -*-
import argparse
import json
import os

from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

from step_00_cache_contracts_files import CONTRACT_URLS

ELASTIC_HOST = os.environ.get("ELASTIC_HOST", "localhost")
ELASTIC_PORT = os.environ.get("ELASTIC_PORT", 9200)
ELASTIC_INDEX_ES = "contracts_es"
ELASTIC_INDEX_EU = "contracts_eu"


def get_elastic_config():
    conf = {}
    conf["host"] = ELASTIC_HOST
    conf["port"] = ELASTIC_PORT
    conf["index_es"] = ELASTIC_INDEX_ES
    conf["index_eu"] = ELASTIC_INDEX_EU
    return conf


def connect(conf):
    es = Elasticsearch(
        host=conf["host"],
        port=conf["port"],
    )
    return es


def index_doc(doc, language="es"):
    conf = get_elastic_config()
    es = connect(conf)
    es.index(index=conf[f"index_{language}"], id=doc["id"], body=doc)


class ContractIndexer:
    def __init__(self, year):
        self.year = year

    def generate_actions(self, language):
        base_folder = f"processed/contracts/{year}"
        for folder in os.listdir(base_folder):
            if os.path.isdir(f"{base_folder}/{folder}/{language}"):
                contract = self.get_contract(f"{base_folder}/{folder}/{language}")
                if contract:
                    yield contract

    def index_contracts(self):
        client = connect(get_elastic_config())
        for language in ["es", "eu"]:
            successes = 0
            print(f"Indexing {language}...")
            for ok, action in streaming_bulk(
                client=client,
                index=get_elastic_config().get(f"index_{language}"),
                actions=self.generate_actions(language),
            ):
                successes += ok
            print(f"Indexed {language}: {successes} items")

    def get_contract(self, folder):
        contract_filename = f"{folder}/contract.json"

        if os.path.exists(contract_filename):
            with open(contract_filename, "r") as fp:
                return json.load(fp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index contracts in Elastic")
    parser.add_argument("year", help="Enter the year to parse")

    myargs = parser.parse_args()

    year = myargs.year

    if year not in CONTRACT_URLS.keys():
        print(
            "Year must be one of the followings: {}".format(
                ",".join(CONTRACT_URLS.keys())
            )
        )
    else:
        cp = ContractIndexer(year)
        cp.index_contracts()
