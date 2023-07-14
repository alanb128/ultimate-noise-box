#!/bin/bash

FILE=/usr/src/app/assets.txt
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    echo "$FILE does not exist. Performing initial setup."
    touch "${FILE}"
    mkdir -p /data/my_data/assets
    mv ./assets/*.jpg /data/my_data/assets
fi

python3 controller.py
