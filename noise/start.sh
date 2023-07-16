#!/bin/bash

FILE=/data/my_data/noise.txt
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    echo "$FILE does not exist. Performing initial setup."
    touch "${FILE}"
    mkdir -p /data/my_data/noise
    mv -f ./assets/*.wav /data/my_data/noise
    mv -f ./assets/*.jpg /data/my_data/noise
fi


python3 noise.py
