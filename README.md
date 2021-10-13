# kontrata

A project to download, process and index all contracts published at the [Basque Public Administration Public Contracts
Platform (REVASCON)](https://www.contratacion.euskadi.eus/w32-kpereva/es/y46aRevasconWar/consultaContratosC/filtro?locale=es).

This project has been inspired by [@JaimeObregon](https://twitter.com/JaimeObregon) and [contratoscantabria.es](https://contratosdecantabria.es/)

## Install

You need a recent python version, any version >= 3.7 will do.

Clone this project and create a virtualenv inside it:

``` 

python3 -m venv .

``` 

Then install the required dependencies:

``` 
./bin/pip install -r requirements.txt
```

Run each of the scripts of the pipeline.

```

./bin/python 01-get_contracts.py
./bin/python 02-process_contracts.py
./bin/python 03-index_contracts.py
```

## Elastic

All the data produced in the 2nd step will be indexed in an [Elastic](https://www.elastic.co/es/) service. You will need such a service to run the indexing part.

Have a look at the [sample elastic docker-compose installation](https://github.com/erral/kontrata-docker) that I am using on development.

## Pipeline

1. 01-get_contracts.py

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

2. 02-process_contracts.py

- Read the existing XML files for each contract and build a json file with the relevant data

3. 03-index_contracts.py

- Index all contracts in elastic


## Work in progress

This is a work in progress. The JSON file generated in the 2nd step (and then indexed in the 3rd step) is subject to change.

## License

GPLv3
