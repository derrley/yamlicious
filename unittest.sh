#!/bin/bash

virtualenv venv
source ./venv/bin/activate
python setup.py install
python setup.py test
deactivate
