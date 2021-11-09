# -*- coding: utf-8 -*-
import argparse
import csv
import difflib
import json
import os

from thefuzz import fuzz, process

from step_00_cache_contracts_files import CONTRACT_URLS


class ContractProcessor:
    def __init__(self, year):
        self.year = year
        self.contracts_folder = f"processed/contracts/{year}"
        self.authorities_cifs = self._get_authorities_cifs()
        self.authorities = self._get_authorities_data()

    def _get_authorities_data(self):
        """load the contractors data from cache, and create a dict to have it available during the
        processing process
        """
        contractors_data = {}
        with open("cache/contractors.json") as fp:
            contractors = json.load(fp)
            for contractor in contractors:
                contractors_data[contractor["codPerfil"]] = contractor

        return contractors_data

    def _get_authorities_cifs(self):
        """Using the CSV data of ef4ktur published here:
            https://www.ef4ktur.com/index.php?option=com_content&task=view&id=198&Itemid=314

        build a dict with the name and CIF of every administration.
        """
        contractors_data = {}
        with open("cifs/data.csv") as fp:
            reader = csv.DictReader(fp, delimiter=";")
            for item in reader:
                item_key = " ".join([item["Razón social"], item["Provincia"]])
                contractors_data[item_key] = item

        return contractors_data

    def process_contracts(self):
        for i, folder in enumerate(os.listdir(self.contracts_folder)):
            self.process_contract(f"{self.contracts_folder}/{folder}/es")
            self.process_contract(f"{self.contracts_folder}/{folder}/eu")
            print(f"Done contract {i}")

    def process_contract(self, folder):
        """ load the data for each contract, process it and write it back to the same file """
        language = folder.split("/")[-1]
        fp = open(f"{folder}/contract.json")
        contract = json.load(fp)
        fp.close()
        contract = self.fix_contents(contract, language)
        fp = open(f"{folder}/contract.json", "w")
        json.dump(contract, fp, indent=4)
        fp.close()

    def fix_contents(self, contract, language):
        """some contracting authority data is wrong:
            names are not named as in official names
            no CIFs are present

        In this method we try to fix it
        """

        contract["authority"]["name"] = self.find_correct_name(contract, language)
        contract["authority"]["cif"] = self.find_correct_cif(contract, language)

    def find_correct_name(self, contract_json, language):
        """ Using the authority code, get its correct name from the code -> authority dict"""
        authority_code = contract_json.get("authority", {}).get("code", "")
        if authority_code:
            authority_code = int(authority_code)
            authority_data = self.authorities.get(authority_code, {})
            if authority_data:
                return authority_data.get("nombreLargo{}".format(language.capitalize()))

        return contract_json.get("authority", {}).get("name", "")

    def find_correct_cif(self, contract, language):
        """ find the most similar name in the list of authority_cifs using difflib and return the value of CIF"""
        name = contract["authority"]["name"]

        matches = process.extract(name, self.authorities_cifs.keys())
        # matches = difflib.get_close_matches(name, self.authorities_cifs.keys())
        if matches and matches[0][1] > 85:
            found_match_name = matches[0][0]
            found_match_cif = self.authorities_cifs[found_match_name]["CIF"]
            print(f"Found match for: {name} -> {found_match_name}")
            return found_match_cif
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse contracts and extract valuable information"
    )
    parser.add_argument("--year", help="Enter the year to parse")

    myargs = parser.parse_args()

    year = myargs.year

    if year and year not in CONTRACT_URLS.keys():
        print(
            "Year must be one of the followings: {}".format(
                ",".join(CONTRACT_URLS.keys())
            )
        )
    else:
        if year is not None:
            cp = ContractProcessor(year)
            cp.process_contracts()
        else:
            for year in CONTRACT_URLS.keys():
                print(f"Processing year {year}")
                cp = ContractProcessor(year)
                cp.process_contracts()
                print(f"Done year {year}")