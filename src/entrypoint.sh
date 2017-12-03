#!/bin/sh

#Check if root certificate exist, otherwise  call generation script
curr_dir = `dirname $0`
file = "$curr_dir/rootCA.key"

if test -s "$file"
then
    echo "Root Certificate Exists"
else
    echo "Generating Root Certificate..."
    sh genrc
fi

nginx &
python3 ./kalamari.py
