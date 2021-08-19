FROM balenalib/raspberrypi3-python:3.7-build

RUN apt-get update && apt-get install python3-pygame

RUN pip3 install flask Flask-API

WORKDIR /usr/src/app

COPY *.py ./

CMD [ "python3", "noise.py" ]
