#! /bin/sh
./src/kalamari.py &
sleep 0.1
nosetests --with-coverage --cover-package='.'
