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


CONTRACTORS_URL_1 = "https://www.contratacion.euskadi.eus/w32-kpeperfi/es/ac70cPublicidadWar/busquedaPoderAdjudicador/autocompletePoder?R01HNoPortal=true&q=&c=true&_=1631455831360"
CONTRACTORS_URL_2 = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/busquedaContrato/autocompleteObtenerPoderes?R01HNoPortal=true&q=&c=true&_=1636384471030"


CONTRACT_URLS = {
    "2021": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2021/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2021/opendata/kontratuak.json",
    },
    "2020": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2020/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2020/opendata/kontratuak.json",
    },
    "2019": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2019/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2019/opendata/kontratuak.json",
    },
    "2018": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2018/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2018/opendata/kontratuak.json",
    },
    "2017": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2017/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2017/opendata/kontratuak.json",
    },
    "2016": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2016/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2016/opendata/kontratuak.json",
    },
    "2015": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2015/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2015/opendata/kontratuak.json",
    },
    "2014": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2014/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2014/opendata/kontratuak.json",
    },
    "2013": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2013/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2013/opendata/kontratuak.json",
    },
    "2012": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2012/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2012/opendata/kontratuak.json",
    },
    "2011": {
        "es": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2011/opendata/contratos.json",
        "eu": "https://opendata.euskadi.eus/contenidos/ds_contrataciones/contrataciones_admin_2011/opendata/kontratuak.json",
    },
}


LIMIT = 30

REALLY_DOWNLOADED = 0
COUNT = 0


class IDNotFoundError(Exception):
    pass


class ContractDownloader:
    def __init__(self, year, update=False):
        self.year = year
        self.update = update

    def get_contracts_from_json(self, language):
        """download, cache and extract values from the given JSON url"""
        url = CONTRACT_URLS[self.year][language]
        filename = url.split("/")[-1]

        os.makedirs(f"cache/{self.year}/{language}", exist_ok=True)

        if not self.update:
            if os.path.isfile(f"cache/{self.year}/{language}/{filename}"):
                print(
                    f"{url} already downloaded to cache/{self.year}/{language}/{filename}"
                )
                return

        print(f"Downloading {url}")
        sock = requests.get(url)
        if sock.ok:
            data = sock.text

            if data.startswith("jsonCallback"):
                data_json_txt = data.split("(", 1)[1].strip(");")  # convert to json
            else:
                data_json_txt = data

            with open(f"cache/{self.year}/{language}/{filename}", "w") as cache_file:
                cache_file.write(data_json_txt)

            print(f"File created cache/{self.year}/{language}/{filename}")
        else:
            print(f"Error downloading {url}")

    def get_contracts(self):
        self.get_contracts_from_json("es")
        self.get_contracts_from_json("eu")


def get_contractors():
    """ Download the list of contractors, with their codes and official names """
    items = []
    urls = [CONTRACTORS_URL_1, CONTRACTORS_URL_2]
    for url in urls:
        data = requests.get(url)
        if data.ok:
            items.extend(data.json())

    with open("cache/contractors.json", "w") as fp:
        json.dump(items, fp)


if __name__ == "__main__":
    # for year in CONTRACT_URLS.keys():
    #     cd = ContractDownloader(year)
    #     cd.get_contracts()

    get_contractors()
