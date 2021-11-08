# -*- coding: utf-8 -*-
import argparse
import csv
import json
import os

from step_00_cache_contracts_files import CONTRACT_URLS


class ContractProcessor:
    def __init__(self, year):
        self.year = year
        self.contracts_folder = f"processed/contracts/{year}"
        self.authorities_cifs = self._get_authorities_cifs()

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
        fp = open(f"{folder}/contract.json")
        contract = json.load(fp)
        fp.close()
        contract = self.fix_contents(contract)
        fp = open(f"{folder}/contract.json", "w")
        json.dump(contract, fp, indent=4)
        fp.close()

    def fix_contents(self, contract):
        contract["authority"]["cif"] = self.find_cif(contract["authority"]["name"])

    def find_cif(self, name):
        """ find the most similar name in the list of authority_cifs using difflib and return the value of CIF"""
        import difflib

        from thefuzz import fuzz, process

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
