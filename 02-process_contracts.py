# -*- coding: utf-8 -*-
import codecs
import json
import os
import xmltodict
from utils import print_progress
from xml.parsers.expat import ExpatError

from xml.etree import ElementTree as ET


class WrongXMLFileFormat(Exception):
    """Exception to raise when the XML file is in a wrong format"""


def process_contracts():
    for folder in os.listdir("contracts"):
        try:
            process_contract("contracts/{}/es".format(folder))
            process_contract("contracts/{}/eu".format(folder))
        except NotADirectoryError:
            pass


def clean_float_value(value):
    try:
        new_value = value.replace(".", "").replace(",", ".")
        return float(new_value)
    except:
        return 0.0


def post_process_old_contract(raw_contract_json):
    contract_json = {}
    contract = raw_contract_json["contratacion"]

    contract_json["title"] = contract.get("contratacion_titulo_contrato", "")
    contract_json["authority"] = contract.get(
        "contratacion_autoridad_contratacion", {}
    ).get("valor", "")
    contract_json["budget"] = 0
    contract_json["status"] = contract.get("contratacion_estado_contrato", {}).get(
        "valor", ""
    )
    contract_json["contract_type"] = contract.get("contratacion_tipo_contrato", {}).get(
        "valor", ""
    )
    contract_json["processing_type"] = contract.get("contratacion_tramitacion", {}).get(
        "valor", ""
    )

    # flags = {}
    # contract_json.update(flags)
    offerers = contract.get("licitadores")
    if isinstance(offerers, list):
        contract_json["offerers"] = [
            {
                "name": "",
                "cif": "",
                "sme": "",
                "date": "",
            }
            for offer in offerers
        ]
    else:
        contract_json["offerers"] = []

    formalizations = contract.get("contratacion_informe_adjudicacion_definitiva", {})
    for item in sorted(formalizations.keys()):
        formalization = formalizations[item]
        contract_json[f"winner_{item}"] = {
            "cif": "",
            "name": formalization.get("empresa", ""),
        }
        contract_json[f"resolution_{item}"] = {
            "priceWithVAT": clean_float_value(formalization.get("precioIVA", "")),
        }

    contract_json["id"] = raw_contract_json["id"]

    return contract_json


def post_process_contract(raw_contract_json):
    contract_json = {}

    contract = raw_contract_json["contractingAnnouncement"]["contracting"]

    contract_json["title"] = contract.get("subject", {}).get("#text", "")
    contract_json["authority"] = (
        contract.get("contractingAuthority", {}).get("name", {}).get("#text", "")
    )
    contract_json["budget"] = clean_float_value(
        contract.get("budgetWithVAT", {}).get("#text", "0")
    )
    contract_json["status"] = contract.get("processingStatus", {}).get("#text", "")
    contract_json["contract_type"] = contract.get("contractingType", {}).get(
        "#text", ""
    )
    contract_json["processing_type"] = contract.get("processing", {}).get("#text", "")
    contract_json["adjudication_procedure"] = contract.get(
        "adjudicationProcedure", {}
    ).get("#text", "")

    flags = {flag["@id"]: flag["#text"] for flag in contract["flags"]["flag"]}
    contract_json.update(flags)

    offers = contract.get("offersManagement", {}).get("offerManagement", {})
    if offers:
        if isinstance(offers, dict):
            offers = [offers]

        contract_json["offerers"] = [
            {
                "name": offer.get("name", {}).get("#text", ""),
                "cif": offer.get("cif", {}).get("#text", ""),
                "sme": offer.get("pyme", {}).get("#text", ""),
                "date": offer.get("registerDate", {}).get("#text", ""),
            }
            for offer in offers
        ]
    else:
        contract_json["offerers"] = []

    formalizations = (
        contract.get("formalizations", {})
        and contract.get("formalizations", {}).get("formalization", {})
        or {}
    )

    if formalizations:
        if isinstance(formalizations, dict):
            formalizations = [formalizations]
        for i, formalization in enumerate(formalizations):
            contract_json[f"winner_{i}"] = {
                "cif": formalization["id"]["#text"],
                "name": formalization["businessName"]["#text"],
            }
    else:
        contract_json["winner"] = None

    resolutions = (
        contract.get("resolutions", {})
        and contract.get("resolutions", {}).get("resolution", {})
        or {}
    )
    if resolutions:
        if isinstance(resolutions, dict):
            resolutions = [resolutions]
        for i, resolution in enumerate(resolutions):
            contract_json[f"resolution_{i}"] = {
                "priceWithVAT": clean_float_value(
                    resolution.get("priceWithVAT", {}).get("#text", "0")
                )
            }

    contract_json["id"] = raw_contract_json["id"]

    return contract_json


@print_progress
def process_contract(folder):
    metadata_filename = "{}/metadata.xml".format(folder)
    data_filename = "{}/data.xml".format(folder)
    json_filename = "{}/data.json".format(folder)

    raw_contract_json = build_dict(metadata_filename, data_filename, json_filename)
    if raw_contract_json:
        raw_contract_json["id"] = folder.split("/")[-2]

        try:
            os.makedirs(f"processed/{folder}")
        except FileExistsError:
            pass

        with open("processed/{}/raw_contract.json".format(folder), "w") as fp:
            json.dump(raw_contract_json, fp, indent=4)

        # We have 2 different formats for the data.xml file
        if "contractingAnnouncement" in raw_contract_json:
            contract_json = post_process_contract(raw_contract_json)

        else:
            contract_json = post_process_old_contract(raw_contract_json)

        with open("processed/{}/contract.json".format(folder), "w") as fp:
            json.dump(contract_json, fp, indent=4)

    else:
        print(f"File not found: {data_filename}")


def build_dict(metadata_filename, data_filename, json_filename):
    try:
        with codecs.open(data_filename, "r", "iso-8859-15") as fp:
            text = fp.read()
            if "contractingAnnouncement" in text:
                result = xmltodict.parse(text)
            else:
                result = parse_old_xml(text)

        return result
    except FileNotFoundError:
        return {}
    except ExpatError:
        return {}


def parse_old_xml(text):
    try:
        items = ET.fromstring(text).findall("item")
        result = {}
        for item in items:
            result.update(process_item(item))

        return result
    except ET.ParseError:
        return {}


def process_item(xmlitem):
    key = xmlitem.get("name")
    subitems = xmlitem.findall("value/item")
    if subitems:
        results = {}
        for subitem in subitems:
            results.update(process_item(subitem))
        return {key: results}
    else:
        value = xmlitem.findall("value")
        if value:
            return {key: value[0].text}

    return {}


if __name__ == "__main__":
    process_contracts()
