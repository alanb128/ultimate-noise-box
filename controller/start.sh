#!/bin/bash

FILE=/data/my_data/assets.txt
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    echo "$FILE does not exist. Performing initial setup."
    touch "${FILE}"
    mkdir -p /data/my_data/assets
    mv -f ./assets/*.jpg /data/my_data/assets
fi

python3 controller.py
