# ultimate-noise-box
Turn a Raspberry Pi into the ultimate relaxation machine that plays soothing wav files.

## Overview
Here are the features of the Ultimate Noise Machine:
- Produces CD-quality stereophonic audio.
- Uses real audio samples with gapless undetectable looping
- Line level audio output jack to use with high quality powered speakers
- Intuitive control panel with rotary wheel and LCD screen
- Web-based control too with a responsive UI

This is the full-size unit based on a Raspberry Pi 3 with custom 3D-printed faceplate:

![Large version](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/large-box.jpg)

The smaller version uses smaller buttons and a Raspberry Pi Zero 2W:

![Small version](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/small-outside.jpg)

## Building it

### Parts list

At a minimum, you need a Pi and the audio bonnet specified below. If you don't use the buttons, rotary encoder, or display, you can control the Noise Box from its built-in web page by browsing to the device's IP address or enabling the Public URL feature.

- Raspberry Pi 3, 4, or Zero 2W
- [Adafruit I2S Audio Bonnet](https://www.adafruit.com/product/4037)
- Momentary SPST pushbutton such as [this one](https://www.adafruit.com/product/1504)
- 1.44 inch TFT [LCD screen](https://www.adafruit.com/product/2088)
- [Rotary encoder](https://www.adafruit.com/product/377) (why not get a nice [knob](https://www.adafruit.com/product/2055) too?)
- [I2C Rotary Encoder Breakout](https://www.adafruit.com/product/4991)


### Assembly

Wire the switches into the audio bonnet following the schematic below. You can solder directly into the pads on the bonnet, which show the GPIO number.

![Schematic](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/schematic.png)

Wire the LCD into the bonnet using the diagram for the 1.44" display found [here](https://learn.adafruit.com/adafruit-1-44-color-tft-with-micro-sd-socket/python-wiring-and-setup#st7789-and-st7735-based-displays-3042525).


Solder the rotary encoder to the encoder board as detailed [here](https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder/overview). Finally, wire the rotary encoder board into the bonnet. You could use the Qwiic connector on one end, but either way the INT terminal on the rotary board will need to be wired in to GPIO 17.


![Inside wiring](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/small-inside.jpg)

Attach the audio bonnet to the Pi.

### Case

Use your favorite project case, and to enhance the project, print your own faceplate to mount the controls. You can find STL files in this repo for the 3D faceplates used in the pictures above. Unfortunately [the cases](https://www.radioshack.com/products/radioshack-project-enclosure-6x4x2) used for them no longer appear available from Radio Shack online.

## Software

This project uses the [balena platform](https://www.balena.io/) for ease of deployment, device management and as the best way to run containers on the Pi. Sign up for a free account - the first 10 devices are free and fully featured. After assembling your hardware and creating a balena account, simply click the button below to generate a microSD card image to burn and insert in your Pi:

[![balena deploy button](https://www.balena.io/deploy.svg)](https://dashboard.balena-cloud.com/deploy?repoUrl=https://github.com/alanb128/ultimate-noise-box)

After you create a fleet, add a new device. Choose the type of Pi you'll be using and you can also add your WiFi credentials at this point. You'll be able to download the SD card image after you add the device. You can use [balenaEtcher](https://etcher.balena.io/) to burn your SD card image. After powering on your Pi, it should start downloading the software.

After the software has downloaded, you'll need to go into the device configuration in balenaCloud and add the following configuration variable:

`BALENA_HOST_CONFIG_dtoverlay`

With the value:

`"hifiberry-dac","i2s-mmap"`

If you want to make your own changes to the software, clone this repo and use the [balena CLI](https://github.com/balena-io/balena-cli) to push the modified code to your device.


## Setup and use

The unit comes with nine pre-recorded relaxation sounds. To add more sounds, browse to the device's IP address (you can find it on the dashboard) on port 9000. (i.e. 192.168.1.100:9000 - but use your IP) The initial login for the Minio browser is `myminio`/`myminio123` here you can drag and drop additional sound files. They must be of the following type: uncompressed PCM format wav files. The sound file should be optimized for looping playback. If you would like an accompanying image for each sound file, give it the same name but with a .jpg file extension. Images should be 128x128 pixels. After uploading additional files, you should reboot the device from the balenaCloud dashboard.

You can scroll through the available sounds by rotating the wheel. Push the wheel to play the selected sound. The stop button stops playback of the current sound.

The display button cycles through the volume display and the device info display. You can adjust the volume level with the wheel when the volume bar is displayed, however controlling the actual volume is currently not implemented.

The four preset buttons instantly start playing the preset sound. To store a preset, open the web interface to the device by browsing its IP address (port 80).

![Web page](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/browser-2.png)

Next to each sound you'll see buttons labeled 1 - 4. Click the button number next to a sound to assign it to that preset number.


## How it works

The application is made up of multiple [containers](https://docs.docker.com/get-started/what-is-a-container/) that communicate with each other through APIs and also share a storage volume. This project is a great example of how containers can work together and cleanly separate functionality. Also note how we add entire functionality by pulling images made by the various software authors. 

![Block diagram](https://raw.githubusercontent.com/alanb128/ultimate-noise-box/main/images/block-diagram.jpg)

Here is a summary of the function of each container:


### Noise
This is the Python program that plays back the audio files through the audio block. It uses Pygame to achieve gapless looping playback. The audio files must be in uncompressed PCM wav file format. It exposes an API (using FlaskAPI) 
- `GET /` returns the current status (`status`) and currently playing file (`file`) and a list of valid API calls.
- `POST /play/<noisename>/` immediately starts looping playback of specified noise, and returns the current status (`status`) and currently playing file (`file`)
- `POST /stop/` immediately stops any file playback, and returns the current status (`status`)

Note `<noisename>` and returned file are the name of the noise, with no path or extension, and underscore (_) instead of spaces.

### Webserver
This is a Node/Express webserver that generates a single page for stopping or starting a noise from the library or presets. It is also currently the only place you can assign presets to noises. The four presets mirror the four physical buttons on the hardware control panel. This application uses XMLHttpRequest to communicate with the backend for stopping, starting and assigning presets. It is set to run on port 80 by default and can be made available outside your network if you enable the device's [public URL](https://www.balena.io/docs/learn/develop/runtime/#public-device-urls).

### [Redis](https://redis.io/)
An in-memory data structure store. It can periodically write to the local storage as well. This is used to store and retreive the values of the preset buttons, last volume level and most recently played file.

### [Minio](https://min.io/)
S3 compatible object storage. This provides a web interface for uploading new audio files and their associated jpegs to the device. To access the interface, browse to the local URL using port 9000. To change the username and password, set new values in the `docker-compose.yml` file before first use! (You'll need to clone this repo and push using the CLI in order to do this.)

### Audio
This is the versatile balena [audio block](https://github.com/balenablocks/audio) that runs a PulseAudio server optimized for balenaOS and is the core of [balenaSound](https://sound.balenalabs.io/). We use it here to take care of setting up and routing all audio needs on the Pi hardware, so the noise container just sends its audio here.

### Controller
A custom Python program that responds to button presses on the control panel, reads the rotary dial position and drives the LCD display.


## Credits

Some of the included sounds and their accompanying images were derived from the following royalty-free image and sound libraries:

Waterfall sound by <a href="https://pixabay.com/users/nickype-10327513/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=121190">NickyPe</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=121190">Pixabay</a>

Splash sound by <a href="https://pixabay.com/users/juliush-3921568/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=8004">JuliusH</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=8004">Pixabay</a>

Rain sound by <a href="https://pixabay.com/users/sergei_spas-9611130/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=153416">sergei_spas</a> from <a href="https://pixabay.com/sound-effects//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=153416">Pixabay</a>

Brown image extracted from photo by <a href="https://unsplash.com/@pawel_czerwinski?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Pawel Czerwinski</a> on <a href="https://unsplash.com/backgrounds/colors/brown?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>

Pink noise image extracted from photo by <a href="https://unsplash.com/@joelfilip?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Joel Filipe</a> on <a href="https://unsplash.com/photos/Mbf3xFiC1Zo?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>

Underwater image extracted from photo by <a href="https://unsplash.com/@hisarahlee?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Sarah Lee</a> on <a href="https://unsplash.com/photos/QURU8IY-RaI?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>

Rain image extracted from photo by <a href="https://unsplash.com/@janfillem?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Jan-Willem</a> on <a href="https://unsplash.com/photos/FobwhDUgdrk?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
  
Splash image extracted from photo by <a href="https://unsplash.com/@amadejtauses?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Amadej Tauses</a> on <a href="https://unsplash.com/photos/xWOTojs1eg4?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>

Waterfall photo by <a href="https://unsplash.com/@nathananderson?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Nathan Anderson</a> on <a href="https://unsplash.com/wallpapers/nature/waterfall?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>

