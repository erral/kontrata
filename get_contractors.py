# -*- coding: utf-8 -*-
import requests

CONTRACTORS_URL = "https://www.contratacion.euskadi.eus/w32-kpeperfi/es/ac70cPublicidadWar/busquedaPoderAdjudicador/autocompletePoder?R01HNoPortal=true&q=&c=true&_=1631455831360"

import csv


def download_items():
    data = requests.get(CONTRACTORS_URL)
    json_data = data.json()
    return json_data


def get_contractors():
    items = download_items()
    headers = items[0].keys()
    with open("contractors.csv", "w") as fp:
        csv_writer = csv.DictWriter(fp, fieldnames=headers)
        csv_writer.writeheader()

        csv_writer.writerows(items)


if __name__ == "__main__":
    get_contractors()
