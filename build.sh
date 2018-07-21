#!/usr/bin/env sh

python3 -m unittest discover tests
./polyprofile.py --config cfg/server_config.yaml --serverInfo --destination .
