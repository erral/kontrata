# kontrata

A project to download, process and index all contracts published at the [Basque Public Administration Public Contracts
Platform (REVASCON)](https://www.contratacion.euskadi.eus/w32-kpereva/es/y46aRevasconWar/consultaContratosC/filtro?locale=es).

This project has been inspired by [@JaimeObregon](https://twitter.com/JaimeObregon) and [contratoscantabria.es](https://contratosdecantabria.es/)

## Install

You need a recent python version, any version >= 3.8 will do.

Clone this project and create a virtualenv inside it:

```shell
python3 -m venv .
```

Then install the required dependencies:

```shell
./bin/pip install -r requirements.txt
```

Run each of the scripts of the pipeline.

````shell
./bin/python step_00_cache_contracts_files.py
./bin/python step_01_get_contracts.py --year 2021
./bin/python step_02_process_contracts.py --year 2021
./bin/python step_03_build_data_dicts.py
./bin/python step_04_fix_authority_and_company_data_async.py --year 2021
./bin/python step_05_index_contracts.py --year 2021

The first script is optional, it just downloads the main files from the opendata portal and caches them locally.
If you don't want to run them, just skip that part and run the step_01 script, it will download the requested year's file. I think
that pre-caching files can speed up the download and processing time, because you can run several parallel downloads.

## Elastic

All the data produced in the 2nd step will be indexed in an [Elastic](https://www.elastic.co/es/) service. You will need such a service to run the indexing part.

Have a look at the [sample elastic docker-compose installation](https://github.com/erral/kontrata-docker) that I am using on development.

By default, the 5th step script will try to index the files in an Elastic service running in localhost:9200. You may change this setting an environment var:

```shell
export ELASTIC_HOST=10.0.0.1 && python step_05_index_contracts.py
````

You have the following variables to customize this:

- ELASTIC_HOST
- ELASTIC_PORT

## Pipeline

0. step_00_cache_contracts_files.py (optional)

- Download and cache the original JSON files

1. step_01_get_contracts.py

It has an optional parameter --year, to download contracts just from that year.
It has an optional parameter --update, to signal if you want to update already downloaded files.

- Download the original contracts JSONP file
- Cache the file
- Convert to JSON
- Cache the file
- For each contract:
  - Create a dir
  - Extract the id
  - Download the data XML file
  - Download the metadata XML file
  - Create the contract JSON file

2. step_02_process_contracts.py

It has an optional parameter --year, to download contracts just from that year.

- Read the existing XML files for each contract and build a json file with the relevant data

3. step_03_build_data_dicts.py

- Build authority and company lists, to use them in the fixing process

4. step_04_fix_authority_and_company_data_async.py

It has an optional parameter --year, to download contracts just from that year.

- Try to fix, unify and calculate cifs and slugs for authority and companies

5. step_05_index_contracts.py

It has an optional parameter --year, to download contracts just from that year.

- Index all contracts in elastic

## Work in progress

This is a work in progress. The JSON file generated in the 2nd step (and then indexed in the 3rd step) is subject to change.

## Demo content

I have downloaded and processed all the data available on the 10th of october and make it available here, in case you do not want to wait to download all of them, I make them available here for anyone here:

- [Full download of the contract files](https://nextcloud.erral.freemyip.com/index.php/s/3G2CRJaomjKWq7Z): 2 XML files (one for data and another one for metadata) and a JSON file with the summary, one per language, a total of 6 files per contract. 665 MB in total.

I have also processed all those files with the second script, and make it available here, in case you do not want to wait to process all of them (the process of the files takes usualy minutes).

- [Full download of the processed contract files](https://nextcloud.erral.freemyip.com/index.php/s/iaLkG7ezCP3jAM4): 2 JSON files, one with the XML in raw JSON (unprocessed, just converted), and another one created after processing the previous one, one per language, a total of 4 files per contract. 286 MB in total.

In the [demo](demo) folder you can find a extract of some contracts with the corresponding files.

## License

GPLv3
