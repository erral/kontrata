from elasticsearch import Elasticsearch

import json
import os

ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200
ELASTIC_INDEX = "contracts"


def get_elastic_config():
    conf = {}
    conf["host"] = ELASTIC_HOST
    conf["port"] = ELASTIC_PORT
    conf["index"] = ELASTIC_INDEX
    return conf


def connect(conf):
    es = Elasticsearch(
        host=conf["host"],
        port=conf["port"],
    )
    return es


def index_doc(doc):
    conf = get_elastic_config()
    es = connect(conf)
    es.index(index=conf["index"], id=doc["id"], body=doc)


def index_contracts():
    for folder in os.listdir("contracts"):
        if os.path.isdir(f"contracts/{folder}/es"):
            index_contract(f"contracts/{folder}/es")


def index_contract(folder):
    contract_filename = f"{folder}/contract.json"

    if os.path.exists(contract_filename):
        with open(contract_filename, "r") as fp:
            index_doc(json.load(fp))


if __name__ == "__main__":
    index_contracts()
