FROM balenalib/raspberrypi3-ubuntu-python:3.7-bionic-build

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y ttf-dejavu libfreetype6-dev

RUN pip3 install pillow RPi.GPIO adafruit-circuitpython-rgb-display requests redis

COPY *.py ./
COPY *.ttf ./

CMD [ "sleep", "infinity" ]

