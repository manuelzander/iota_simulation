# IOTA Tangle simulation in Python

This is a Python implementation of a *single- and multi-agent simulation* of the IOTA Tangle, as described in the [white-papers](https://www.iota.org/foundation/research-papers).

My full thesis is available [here](./thesis_final.pdf). Please cite: _Zander, W. M. (2018). A Multi-Agent Simulation Framework and Analysis of the IOTA Tangle (Unpublished master's thesis). Imperial College London, United Kingdom._

## Prerequisites

![python-1](https://img.shields.io/badge/python-3.6-blue?style=for-the-badge&logo=python&logoColor=white)
![python-2](https://img.shields.io/badge/python-3.7-blue?style=for-the-badge&logo=python&logoColor=white)

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

The code is run and tested with Python 3.6.3 and 3.7 on macOS 10.12.6., 10.13 and 10.14.

### Environment

Clone the repo to your local machine.

Create a virtual environment for Python 3 with:

    python3 -m pip install virtualenv
    python3 -m virtualenv -p python3 env

Activate the virtual environment with:

    source env/bin/activate
    
`pip`'s install of pygraphviz is currently broken, thus run the following before using the makefile:

    brew install graphviz
    pip3 install pygraphviz

Then the used Python libraries/packages can be installed with:

    make

or alternatively with:

    pip3 install -r requirements.txt

## Run the simulation

Run the simulation with:

    python core.py

In this file you can also change the configuration of the simulation.

## Run tests

`pytest` is used for testing.
Run the tests with:

    pytest

## Authors

- Manuel Zander

## License

See [LICENSE](./LICENSE)

## Acknowledgments

Many thanks to [nud3l](https://github.com/nud3l) for his review and great suggestions during development of this software 😊
