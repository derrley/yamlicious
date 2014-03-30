#!/bin/bash

set -e

virtualenv venv
source ./venv/bin/activate
python setup.py install
python setup.py test
python3 setup.py install
python3 setup.py test
deactivate
