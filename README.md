# ultimate-noise-box
Turn a Raspberry Pi 3 into the ultimate noise and relaxation machine.

This is still a work in progress! You can learn more in the ongoing [build log](https://forums.balena.io/t/the-ultimate-diy-noise-machine/344407)

## Overview
Here are the features of the noise machine:
- Produces CD-quality stereophonic audio.
- Usees real audio samples with gapless undetectable looping
- A high quality built-in amplifier and speaker system and/or line level audio output
- Intuitive control panel with rotary wheel and LCD screen
- Web-based control with a responsive UI for any client

![initial plan](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/initial_plan-50.jpeg)

## Containers

### Noise
This is the Python program that plays back the audio files through the audio block. It uses Pygame to achieve gapless looping playback. The audio files must be in uncompressed PCM wav file format. It exposes an API (using FlaskAPI) 
- `GET /` returns the current status (`status`) and currently playing file (`file`) and a list of valid API calls.
- `POST /play/<noisename>/` immediately starts looping playback of specified noise, and returns the current status (`status`) and currently playing file (`file`)
- `POST /stop/` immediately stops any file playback, and returns the current status (`status`)

Note `<noisename>` and returned file are the name of the noise, with no path or extension, and underscore (_) instead of spaces.

### Webserver
This is a Node/Express webserver that generates a single page for stopping or starting a noise from the library or presets. It is alos currently the only place you can assign presets to noises. The four presets mirror the four physical buttons on the hardware control panel. This application uses XMLHttpRequest to communicate with the backend for stopping, starting and assigning presets. It is set to run on port 80 by default and will be displayed if you enable the device's [public URL](https://www.balena.io/docs/learn/develop/runtime/#public-device-urls).

### [Redis](https://redis.io/)
An in-memory data structure store. It can periodically write to the local storage as well. This is used to store and retreive the values of the preset buttons, last volume level and most recently played file.

### [Minio](https://min.io/)
S3 compatible object storage. This provides a web interface for uploading new audio files and their associated jpegs to the device. To access the interface, browse to the local URL using port 9000. To change the username and password, set new values in the `docker-compose.yml` file before first use! (You'll need to clone this repo and push using the CLI in order to do this.)

### Audio
This is our beloved [audio block](https://github.com/balenablocks/audio) that runs a PulseAudio server optimized for balenaOS and is the core of [balenaSound](https://sound.balenalabs.io/). We use it here to take care of setting up and routing all audio needs on the Pi hardware, so the noise container just sends its audio here.

### Controller (coming soon)
A custom Python program that responds to button presses on the control panel, reads the rotary dial position and drives the LCD display.

## How to use
(coming soon)
