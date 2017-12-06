#!/bin/sh

if [ ! -r ca.key ] || [ ! -r ca.crt ]; then
    sh genrc.sh
fi

nginx &
python3 ./kalamari.py
