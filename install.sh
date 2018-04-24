#!/usr/bin/env sh

pip3 install -r requirements.txt --user
./polyprofile.py -c cfg/config.yaml -d .
