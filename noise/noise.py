#!/usr/bin/python

from flask import request
from flask_api import FlaskAPI
import pygame
from pathlib import Path

noise_path = "/data/my_data/noise/"
file_filter = "wav"
now_playing = "(nothing)"
noise_status = "stop"

pygame.init()
pygame.mixer.init()

app = FlaskAPI(__name__)

@app.route('/', methods=["GET"])
def api_root():
    global noise_status, now_playing
    return {
           "play_url_POST": request.url + "play/(noise_name)/",
           "stop_url_POST": request.url + "stop/",
           "status": noise_status,
           "file": now_playing
           }
  
@app.route('/play/<noisename>/', methods=["GET", "POST"])
def api_pygame_play(noisename):
    global noise_status, now_playing
    if request.method == "POST":
        my_file = noise_path + noisename + '.' + file_filter
        check_file = Path(my_file)
        if check_file.is_file():
            now_playing = noisename
            pygame.mixer.music.load(my_file)
            pygame.mixer.music.play(-1)
            noise_status = "play"
        else:
            now_playing = "(nothing)"
            return {
                  "status": "error",
                  "file": noisename
                   }
    return {
           "status": noise_status,
           "file": noisename
           }

@app.route('/stop/', methods=["POST"])
def api_pygame_stop():
    global noise_status, now_playing
    pygame.mixer.music.stop()
    now_playing = "(nothing)"
    noise_status = "stop"
    return {"status": "stop"}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
