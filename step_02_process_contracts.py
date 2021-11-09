# -*- coding: utf-8 -*-
import csv
import argparse
import codecs
import datetime
import json
import os
import re
from xml.etree import ElementTree as ET
from xml.parsers.expat import ExpatError

import xmltodict

from step_00_cache_contracts_files import CONTRACT_URLS

TRUE_BOOL_VALUES = ["sí", "si", "bai"]


def clean_bool_value(value):
    if isinstance(value, str):
        return value.lower() in TRUE_BOOL_VALUES

    return False


def clean_float_value(value):
    # We have several cases here:
    #         202.49
    #   1.555.092
    #       6.824,37
    #         306
    #     3844443
    #      10.030,9
    #       4.268.35
    #
    # this will catch every entire number, except the decimal part
    if isinstance(value, str):
        entires_re = r"^(\d*([\,\.]?\d{3})*)+"
        entires = re.search(entires_re, value)
        # this will catch any decimal part, if it comes
        decimals_re = r"[\,\.]([0-9]{1,2})?$"
        decimals = re.search(decimals_re, value)
        value = re.sub("[^0-9]", "", entires.group(0)) + (
            decimals.group(0) if decimals else ""
        )
        # we replace the decimal separator , with . for safety
        value = value.replace(",", ".")
        return float(value)
    return None


def clean_float_value_old_xml(value):
    # Here in all cases . is used as a thousands separator, and , as a decimal separator
    # 1.216.511,05
    #     2.076,48
    #       275
    #
    try:
        new_value = value.replace(".", "").replace(",", ".")
        return float(new_value)
    except:
        return 0.0


def clean_date_value(value):
    """
    Available date formats:
        - dd/mm/yyyy
        - yyyy/mm/dd
    """

    if value and value.find("/") != -1:
        # First remove the time part if present
        value_str = value.split(" ")[0]
        date_parts = value_str.split("/")
        if len(date_parts) == 3:
            try:
                if date_parts[0].isdigit() and int(date_parts[0]) > 999:
                    # The format is yyyy/mm/dd
                    return datetime.date(
                        int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    ).isoformat()
                elif date_parts[2].isdigit() and int(date_parts[2]) > 999:
                    # The format is dd/mm/yyyy
                    return datetime.date(
                        int(date_parts[2]), int(date_parts[1]), int(date_parts[0])
                    ).isoformat()
            except ValueError:
                print(f"ERROR PARSING DATE {value}")
                return None

    return None


def extract_value_from_flags(flags, flagname):
    for flag in flags:
        if flag["@id"] == flagname:
            return flag["#text"] == "true"

    return None


class WrongXMLFileFormat(Exception):
    """Exception to raise when the XML file is in a wrong format"""


class ContractProcessor:
    def __init__(self, year):
        self.year = year
        self.contracts_folder = f"contracts/{year}"
        os.makedirs(f"processed/{self.contracts_folder}", exist_ok=True)

    def process_contracts(self):
        for count, folder in enumerate(os.listdir(self.contracts_folder)):
            try:
                self.process_contract(f"{self.contracts_folder}/{folder}/es")
                self.process_contract(f"{self.contracts_folder}/{folder}/eu")
                print(f"Processed {count} contracts")
            except NotADirectoryError:
                pass

    def process_contract(self, folder):
        metadata_filename = f"{folder}/metadata.xml"
        data_filename = f"{folder}/data.xml"
        json_filename = f"{folder}/data.json"

        raw_contract_json = self.build_dict(
            metadata_filename, data_filename, json_filename
        )
        if raw_contract_json:
            raw_contract_json["id"] = folder.split("/")[-2]

            os.makedirs(f"processed/{folder}", exist_ok=True)

            with open(f"processed/{folder}/raw_contract.json", "w") as fp:
                json.dump(raw_contract_json, fp, indent=4)

            # We have 2 different formats for the data.xml file
            if "contractingAnnouncement" in raw_contract_json:
                contract_json = self.post_process_contract(raw_contract_json)
            else:
                contract_json = self.post_process_old_contract(raw_contract_json)

            contract_json["year"] = self.year

            with open(f"processed/{folder}/contract.json", "w") as fp:
                json.dump(contract_json, fp, indent=4)

        else:
            print(f"File not found: {data_filename}")

    def post_process_old_contract(self, raw_contract_json):
        contract_json = {}
        contract = raw_contract_json["contratacion"]

        contract_json["title"] = contract.get("contratacion_titulo_contrato", "")
        authority_name = contract.get("contratacion_autoridad_contratacion", {}).get(
            "valor", ""
        ) or contract.get("contratacion_poder_adjudicador", {}).get("valor", "")
        authority_cif = contract.get("contratacion_autoridad_contratacion", {}).get(
            "valor", ""
        ) or contract.get("contratacion_poder_adjudicador", {}).get(
            "contratacion_nifcif", ""
        )
        authority_code = contract.get("contratacion_poder_adjudicador", {}).get(
            "codigo", ""
        )
        contract_json["authority"] = {
            "name": authority_name,
            "cif": authority_cif,
            "code": authority_code,
        }

        contract_json["budget"] = clean_float_value(
            contract.get("contratacion_presupuesto_contrato_con_iva_cab", {})
        )
        status_name = contract.get("contratacion_estado_tramitacion", {}).get(
            "valor", ""
        )
        status_code = contract.get("contratacion_estado_tramitacion", {}).get(
            "codigo", ""
        )

        contract["status"] = {
            "name": status_name,
            "code": status_code,
        }

        contract_type_name = contract.get("contratacion_tipo_contrato", {}).get(
            "valor", ""
        )
        contract_type_code = contract.get("contratacion_tipo_contrato", {}).get(
            "codigo", ""
        )

        contract_json["contract_type"] = {
            "name": contract_type_name,
            "code": contract_type_code,
        }

        processing_type_name = contract.get("contratacion_tramitacion", {}).get(
            "valor", ""
        )

        processing_type_code = contract.get("contratacion_tramitacion", {}).get(
            "codigo", ""
        )

        contract_json["processing_type"] = {
            "name": processing_type_name,
            "code": processing_type_code,
        }

        adjudication_procedure_name = contract.get(
            "contratacion_procedimiento", {}
        ).get("valor", "")

        adjudication_procedure_code = contract.get(
            "contratacion_procedimiento", {}
        ).get("codigo", "")

        contract_json["adjudication_procedure"] = {
            "name": adjudication_procedure_name,
            "code": adjudication_procedure_code,
        }

        contract_json["minor_contract"] = clean_bool_value(
            contract.get("contratacion_contrato_menor", "").lower()
        )

        # flags = {}
        # contract_json.update(flags)
        offerers = contract.get("contratacion_empresas_licitadoras")
        if isinstance(offerers, dict):
            offerers = [offerers]
        if isinstance(offerers, list):
            contract_json["offerers"] = [
                {
                    "name": offer.get(
                        "contratacion_empresa_licitadora_razon_social", ""
                    ),
                    "cif": offer.get("contratacion_empresa_licitadora_cif", ""),
                    "sme": clean_bool_value(
                        offer.get("contratacion_empresa_licitadora_pyme", "")
                    ),
                    "date": None,
                }
                for offer in offerers
            ]
        else:
            contract_json["offerers"] = []

        contract_json["offerer_count"] = contract.get(
            "contratacion_num_licitadores", ""
        )

        formalizations = contract.get(
            "contratacion_informe_adjudicacion_definitiva", {}
        )
        for item in sorted(formalizations.keys()):
            formalization = formalizations[item]
            contract_json[f"winner_{item}"] = {
                "cif": "",
                "name": formalization.get("empresa", ""),
            }
            contract_json[f"resolution_{item}"] = {
                "priceWithVAT": clean_float_value_old_xml(
                    formalization.get("precioIVA", "")
                ),
            }

        contract_json["adjudication_date"] = clean_date_value(
            contract.get("contratacion_fecha_adjudicacion_definitiva", "")
        )

        contract_json["id"] = raw_contract_json["id"]

        return contract_json

    def post_process_contract(self, raw_contract_json):
        contract_json = {}

        contract = raw_contract_json["contractingAnnouncement"]["contracting"]

        contract_json["title"] = contract.get("subject", {}).get("#text", "")
        authority_name = (
            contract.get("contractingAuthority", {}).get("name", {}).get("#text", "")
        )
        authority_cif = ""

        authority_code = contract.get("contractingAuthority", {}).get("@id", "")

        contract_json["authority"] = {
            "name": authority_name,
            "cif": authority_cif,
            "code": authority_code,
        }
        contract_json["budget"] = clean_float_value_old_xml(
            contract.get("budgetWithVAT", {}).get("#text", "0")
        )

        status_name = contract.get("processingStatus", {}).get("#text", "")
        status_code = contract.get("processingStatus", {}).get("@id", "")

        contract_json["status"] = {
            "name": status_name,
            "code": status_code,
        }

        contract_type_name = contract.get("contractingType", {}).get("#text", "")
        contract_type_code = contract.get("contractingType", {}).get("@id", "")

        contract_json["contract_type"] = {
            "name": contract_type_name,
            "code": contract_type_code,
        }

        processing_name = contract.get("processing", {}).get("#text", "")
        processing_code = contract.get("processing", {}).get("@id", "")

        contract_json["processing_type"] = {
            "name": processing_name,
            "code": processing_code,
        }

        adjudication_procedure_name = contract.get("adjudicationProcedure", {}).get(
            "#text", ""
        )

        adjudication_procedure_code = contract.get("adjudicationProcedure", {}).get(
            "@id", ""
        )

        contract_json["adjudication_procedure"] = {
            "name": adjudication_procedure_name,
            "code": adjudication_procedure_code,
        }

        contract_json["minor_contract"] = extract_value_from_flags(
            contract["flags"]["flag"], "contrato_menor"
        )

        offers = contract.get("offersManagement", {}).get("offerManagement", {})
        if offers:
            if isinstance(offers, dict):
                offers = [offers]

            contract_json["offerers"] = [
                {
                    "name": offer.get("name", {}).get("#text", ""),
                    "cif": offer.get("cif", {}).get("#text", ""),
                    "sme": clean_bool_value(offer.get("pyme", {}).get("#text", "")),
                    "date": clean_date_value(
                        offer.get("registerDate", {}).get("#text", "")
                    ),
                }
                for offer in offers
            ]
        else:
            contract_json["offerers"] = []

        contract_json["offerer_count"] = contract.get("biddersNumber", {}).get(
            "#text", 0
        )

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
                contract_json["adjudication_date"] = clean_date_value(
                    resolution.get("adjInfo", {}).get("date", {}).get("#text", "")
                )

        contract_json["id"] = raw_contract_json["id"]

        return contract_json

    def build_dict(self, metadata_filename, data_filename, json_filename):
        try:
            with codecs.open(data_filename, "r", "iso-8859-15") as fp:
                text = fp.read()
                if "contractingAnnouncement" in text:
                    result = xmltodict.parse(text)
                else:
                    result = self.parse_old_xml(text)

            return result
        except FileNotFoundError:
            return {}
        except ExpatError:
            return {}

    def parse_old_xml(self, text):
        try:
            items = ET.fromstring(text).findall("item")
            result = {}
            for item in items:
                result.update(self.process_item(item))

            return result
        except ET.ParseError:
            return {}

    def process_item(self, xmlitem):
        key = xmlitem.get("name")
        subitems = xmlitem.findall("value/item")
        if subitems:
            results = {}
            for subitem in subitems:
                results.update(self.process_item(subitem))
            return {key: results}
        else:
            value = xmlitem.findall("value")
            if value:
                return {key: value[0].text}

        return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse contracts and extract valuable information"
    )
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
        cp = ContractProcessor(year)
        cp.process_contracts()
