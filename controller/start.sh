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

# On slower devices, Supervisor API needs time to start
# You can remove delay below on Pi 3B+ or newer
echo "Waiting 45 seconds for supervisor to start..."
sleep 45
echo "Starting controller"

python3 controller.py

#sleep infinity
