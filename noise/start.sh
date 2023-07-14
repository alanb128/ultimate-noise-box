#!/bin/bash

FILE=/usr/src/app/noise.txt
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    echo "$FILE does not exist. Performing initial setup."
    touch "${FILE}"
    mkdir -p /data/my_data/noise
    mv *.wav /data/my_data/noise
fi


python3 noise.py
