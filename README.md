# ultimate-noise-box
Turn a Raspberry Pi 3 into the ultimate noise and relaxation machine.

This is still a work in progress! You can learn more in the ongoing [build log](https://forums.balena.io/t/the-ultimate-diy-noise-machine/344407)

## The plan
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

Note <<noisename>> and returned file are the name of the noise, with no path or extension, and underscore (_) instead of spaces.
