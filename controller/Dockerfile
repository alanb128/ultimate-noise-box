FROM balenalib/raspberrypi3-ubuntu-python:3.7-bionic-build-20210826

WORKDIR /usr/src/app

RUN \
    apt-get update && apt-get install -y ttf-dejavu libfreetype6-dev

RUN \
    pip3 install numpy pillow RPi.GPIO adafruit-circuitpython-rgb-display \
    requests redis adafruit-circuitpython-seesaw

# *** tested versions of above libraries ***
# numpy 1.21.5
# pillow 9.1.0
# RPi.GPIO 0.7.1
# adafruit-circuitpython-rgb-display 3.10.12
# requests 2.27.1
# redis 4.2.2
# adafruit-circuitpython-seesaw 1.10.8

COPY *.py ./
COPY *.ttf ./

CMD [ "python3", "controller.py" ]
