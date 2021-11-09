# -*- coding: utf-8 -*-
import argparse
import csv
import difflib
import json
import os

from thefuzz import fuzz, process

from step_00_cache_contracts_files import CONTRACT_URLS


class ContractProcessor:
    def __init__(self):
        self.authorities = {}
        self.companies = {}
        self.companies_names = {}

    def process_contracts(self):
        for year in CONTRACT_URLS.keys():
            print(f"Processing year {year}")
            self.contracts_folder = f"processed/contracts/{year}"
            try:
                for i, folder in enumerate(os.listdir(self.contracts_folder)):
                    self.process_contract(f"{self.contracts_folder}/{folder}/es")
                    self.process_contract(f"{self.contracts_folder}/{folder}/eu")
                    print(f"Done contract {i}")
            except FileNotFoundError:
                pass

            print(f"Done year {year}")

        self.dump_files()

    def process_contract(self, folder):
        try:
            language = folder.split("/")[-1]
            with open(f"{folder}/contract.json") as fp:
                contract = json.load(fp)
                self.extract_contents(contract, language)
        except FileNotFoundError:
            print(f"No contract for {folder}")

    def dump_files(self):
        with open("cache/authorities.json", "w") as fp:
            json.dump(self.authorities, fp, indent=4)

        with open("cache/companies.json", "w") as fp:
            json.dump(self.companies, fp, indent=4)

        with open("cache/companies_names.json", "w") as fp:
            json.dump(self.companies_names, fp, indent=4)

    def extract_contents(self, contract, language):
        """ extract the main data for authorities and companies, to have a single source of truth"""
        self.extract_authorities(contract, language)
        self.extract_companies(contract, language)

    def extract_authorities(self, contract, language):
        authority = contract["authority"]
        self.add_authority(authority, language)

    def extract_companies(self, contract, language):
        for key in contract.keys():
            if key.startswith("winner_"):
                self.add_company(contract[key], language)

    def add_authority(self, authority, language):
        if authority["code"] not in self.authorities:
            self.authorities[authority["code"]] = {}
            self.authorities[authority["code"]][language] = authority

        else:
            self.merge_authority(authority, language)

    def merge_authority(self, authority, language):
        saved_authority = self.authorities[authority["code"]]
        if language not in saved_authority:
            self.authorities[authority["code"]][language] = authority
        else:
            self.merge_authority_per_languages(authority, language)

    def merge_authority_per_languages(self, authority, language):
        saved_authority = self.authorities[authority["code"]][language]
        for key, value in saved_authority.items():
            if not value:
                saved_authority[key] = authority[key]

        self.authorities[authority["code"]][language] = saved_authority

    def add_company(self, company, language):
        if company["cif"] and company["cif"] not in self.companies:
            self.companies[company["cif"]] = company
        elif not company["cif"]:
            self.companies_names[company["name"]] = company


if __name__ == "__main__":
    cp = ContractProcessor()
    cp.process_contracts()
