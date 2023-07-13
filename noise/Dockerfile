FROM balenalib/raspberrypi3-python:3.7-build-20210705

RUN apt-get update && apt-get install python3-pygame

RUN pip3 install flask Flask-API

# Tested versions:
# flask 2.0.2
# Flask-API 3.0.post1

WORKDIR /usr/src/app

COPY *.py ./
COPY *.sh ./

CMD [ "bash", "start.sh" ]
