from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

import json
import os

ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200
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


def generate_actions(language):
    for folder in os.listdir("processed/contracts"):
        if os.path.isdir(f"processed/contracts/{folder}/{language}"):
            contract = get_contract(f"processed/contracts/{folder}/{language}")
            if contract:
                yield contract


def index_contracts():
    client = connect(get_elastic_config())
    for language in ["es", "eu"]:
        successes = 0
        print(f"Indexing {language}...")
        for ok, action in streaming_bulk(
            client=client,
            index=get_elastic_config().get(f"index_{language}"),
            actions=generate_actions("es"),
        ):
            successes += ok
        print(f"Indexed {language}: {successes} items")


def index_contract_old(folder, language="es"):
    contract_filename = f"{folder}/contract.json"

    if os.path.exists(contract_filename):
        with open(contract_filename, "r") as fp:
            index_doc(json.load(fp), language)


def get_contract(folder):
    contract_filename = f"{folder}/contract.json"

    if os.path.exists(contract_filename):
        with open(contract_filename, "r") as fp:
            return json.load(fp)


if __name__ == "__main__":
    index_contracts()
