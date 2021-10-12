import digitalio 
import board 
from PIL import Image, ImageDraw, ImageFont 
import adafruit_rgb_display.ili9341 as ili9341 
import adafruit_rgb_display.st7789 as st7789 # pylint: disable=unused-import 
import adafruit_rgb_display.hx8357 as hx8357 # pylint: disable=unused-import 
import adafruit_rgb_display.st7735 as st7735 # pylint: disable=unused-import 
import adafruit_rgb_display.ssd1351 as ssd1351 # pylint: disable=unused-import 
import adafruit_rgb_display.ssd1331 as ssd1331 # pylint: disable=unused-import
import time 
import subprocess 
import datetime 
import RPi.GPIO as GPIO 
import requests
import redis 
import os


# TFT configuration for CS and DC pins:
cs_pin = digitalio.DigitalInOut(board.CE0) #pin24
dc_pin = digitalio.DigitalInOut(board.D25) #pin22
reset_pin = digitalio.DigitalInOut(board.D24) #pin18

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# pylint: disable=line-too-long
# Create the display:
# disp = st7789.ST7789(spi, rotation=90,                            # 2.0" ST7789
# disp = st7789.ST7789(spi, height=240, y_offset=80, rotation=180,  # 1.3", 1.54" ST7789
# disp = st7789.ST7789(spi, rotation=90, width=135, height=240, x_offset=53, y_offset=40, # 1.14" ST7789
# disp = hx8357.HX8357(spi, rotation=180,                           # 3.5" HX8357
# disp = st7735.ST7735R(spi, rotation=90,                           # 1.8" ST7735R
disp = st7735.ST7735R(spi, rotation=270, height=128, x_offset=2, y_offset=3,   # 1.44" ST7735R
# disp = st7735.ST7735R(spi, rotation=90, bgr=True,                 # 0.96" MiniTFT ST7735R
# disp = ssd1351.SSD1351(spi, rotation=180,                         # 1.5" SSD1351
# disp = ssd1351.SSD1351(spi, height=96, y_offset=32, rotation=180, # 1.27" SSD1351
# disp = ssd1331.SSD1331(spi, rotation=180,                         # 0.96" SSD1331
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
if disp.rotation % 180 == 90:
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
else:
    width = disp.width  # we swap height/width to rotate it to landscape!
    height = disp.height

# Main RGB image
image = Image.new("RGB", (width, height))

# image for info area
img_info = Image.new("RGB", (128, 20), (0, 0, 0))

# create idle image
idle_image = Image.new("RGB", (width, height))

# Drawing object for main display image
draw = ImageDraw.Draw(image)

wav_list = []  # list of available wav files to play (strings)
img_list = []  # list of images to display for each wav file (images)
vol_list = []  # list of volume bars representing volumes (images)
#wav_pointer = 0  # index of curently displayed wav when rotating wheel (int)
noise_pointer = 0  # index of currently displayed noise image when rotating wheel (int)
now_playing = ""  # name of currently playing file or emply string
display_mode = 0  # int display mode (0-2)
in_button = 0  # a test for debouncing
current_volume = 10  # current volume (0-20)

IMAGE_PATH = "/data/my_data/noise/"  # string path to images
TEXT_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
ICON_FONT = ImageFont.truetype("/usr/src/app/materialdesignicons-webfont.ttf", 20)
DEBOUNCE = 600  # switch debounce time in ms

print(os.getenv('BALENA_SUPERVISOR_ADDRESS', 'no supv addr'))
print(os.getenv('BALENA_SUPERVISOR_API_KEY', 'no api key'))
def lib_setup():
    #
    # Generate list of all sound files available,
    # create list of all images with titles burned in,
    # create volume image list
    #
    global wav_list, img_list, img_info
    # Get all sound files in folder
    dir_list = os.listdir(IMAGE_PATH)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    # for each file:
    for d in dir_list:
        if d[-4:] == ".wav":
            save_image = Image.new("RGB", (width, height))
            save_draw = ImageDraw.Draw(save_image)
            save_draw.rectangle((0, 0, width, height), fill=(0, 0, 0)) # draw black box
            noise_name = d[:len(d) - 4]
            wav_list.append(noise_name)
            try:
                i = Image.open(IMAGE_PATH + noise_name + ".jpg")
            except:
                i = Image.open(IMAGE_PATH + "default.jpg")
            save_image.paste(i, (0,0))
            save_image.paste(img_info, (0, 108))
            text = noise_name.replace("_", " ")
            save_draw.text((20, 110), text, font=font, fill=(255, 255, 255),)
            img_list.append(save_image)
            #print(wav_list)
            #print(img_list)
    # generate a list of 20 vol images:
    for v in range(0, 19):
        save_image = Image.new("RGB", (width, height))
        save_draw = ImageDraw.Draw(save_image)
        save_draw.rectangle((0, 0, width, height), fill=(0, 0, 0))  # draw black box
        i = Image.open(IMAGE_PATH + "vol_" + "{:0>3}".format(v * 5) + ".jpg")
        save_image.paste(i, (0,50))
        text = "volume: " + str(v * 5) + " %"
        save_draw.text((20, 110), text, font=font, fill=(255, 255, 255),)
        vol_list.append(save_image)

def create_idle_image():
    #
    # Create the idle image!
    #
    global idle_image
    idle_image_raw = Image.open(IMAGE_PATH + "idle.jpg")
    idle_image.paste(idle_image_raw, (0,0))  # use idle image
    idle_draw = ImageDraw.Draw(idle_image)
    idle_image.paste(img_info, (0, 108))
    idle_draw.text((1, 110), "\U000F04DB", font=ICON_FONT, fill=(255, 255, 255),)  # draw the stop icon
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    idle_draw.text((20, 110), "(idle)", font=font, fill=(255, 255, 255),)

# Setup initial state
def init_controller():
    print("init display")
    global disp, image, draw, width, now_playing, idle_image

    # Draw a blue box for init display
    draw.rectangle((0, 0, width, height), fill=(0, 153, 153))

    # Load a TTF Font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

    # Draw splash screen
    text = "Welcome!"
    draw.text((5, 10), text, font=font, fill=(255, 255, 0),)
    disp.image(image)
    #time.sleep(2)
    lib_setup()
    create_idle_image()

    # get current status
    r = requests.get('http://noise:5000/')
    j = r.json()

    print(j)
    if j["status"] == "stop":
        now_playing = ""
        display_now(idle_image)
    else:
        now_playing = j["file"]
        print("now playing: ", now_playing)
        display_now(img_list[wav_list.index(now_playing)])

def display_info():
    #
    # Display device info on LCD
    #
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))  # draw black box
    #image.paste(img_list[wav_pointer], (0,0))  # use now playing image
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    draw.text((1, 60), "INFO coming soon!", font=font, fill=(255, 255, 255),)  # draw the rotate icon
    disp.image(image)

def button_stop(channel):
    #
    # stop payback
    #
    r = requests.post('http://noise:5000/stop/')
    print("Stop button pressed.")
    now_playing = ""
    display_now(idle_image)

def button_display(channel):
    #
    # change display mode
    #
    global display_mode
    display_mode = display_mode + 1
    if display_mode == 3:
        display_mode = 0
    # Decide what to display
    if display_mode == 0:
        display_now(img_list[wav_list.index(now_playing)])
    elif display_mode == 1:
        image.paste(vol_list[current_volume], (0,0))
        disp.image(image)
    else:
        display_info()
    print("Display mode {0}".format(display_mode))

def button_preset(channel):
    #
    # play a preset
    #
    # get preset number (1-4) from channel
    preset_channel = [6, 13, 19, 26]
    presety = preset_channel.index(channel)
    # get preset name value from redis
    r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    p = r.get("p" + str(presety + 1))
    print("Preset {0} ({1}) pressed.".format(p, presety))
    # play/display the file image
    text_icon = ["\U000F03A4", "\U000F03A7", "\U000F03AA", "\U000F03AD"]
    play_file(p, text_icon[presety])

def button_rotary_click(channel):
    # rotary clicked
    #time.sleep(0.2)
    global display_mode
    print("Rotary button click.")
    # decide what to do:
    if display_mode == 0:
        if wav_list[noise_pointer] != now_playing:
            play_file(wav_list[noise_pointer])
    else:  # change display mode
        button_display(0)

def play_file(noise_name, extra_icon=""):
    #
    # Play the specified file, update the display
    #
    global now_playing, noise_pointer, display_mode
    display_mode = 0
    now_playing = noise_name
    noise_pointer = wav_list.index(now_playing)
    r = requests.post('http://noise:5000/play/' + now_playing + "/")
    display_now(img_list[wav_list.index(now_playing)], extra_icon)

def display_now(d_img, extra_icon=""):
    #
    # sends specified image to lcd display
    # if "" then display idle image
    #
    global disp, image, draw

    # Draw icon
    #draw.text((20, 110), text, font=font, fill=(255, 255, 255),)
    #print("Extra icon: {0}".format(extra_icon))
    image.paste(d_img, (0,0))  # use now playing image
    #print("Now playing: {0}, wav_list.index(now_playing): {1}".format(now_playing, wav_list.index(now_playing)))
    draw.text((1, 110), "\U000F040A", font=ICON_FONT, fill=(255, 255, 255),)  # draw the play icon
    if len(extra_icon) > 0:   # draw the extra icon
        draw.text((105, 5), extra_icon, font=ICON_FONT, fill=(255, 255, 255),)  # draw the play icon

    disp.image(image)

def wheel_right(channel):
    #
    # Wheel turned right (>)
    #
    #global counter, step, wav_pointer, ICON_FONT, image, draw, disp, current_volume
    global noise_pointer, current_volume

    clkState = GPIO.input(18)
    dtState = GPIO.input(17)

    if clkState == 0 and dtState == 1:
        print("Wheel turned right.")
        if display_mode == 0:
            noise_pointer = noise_pointer + 1
            if noise_pointer > len(img_list) - 1:
                noise_pointer = 0
            image.paste(img_list[noise_pointer], (0,0))  # use now playing image
            #print("Now playing: {0}, wav_list.index(now_playing): {1}".format(now_playing, wav_list.index(now_playing)))
            draw.text((1, 110), "\U000F04D7", font=ICON_FONT, fill=(255, 255, 255),)  # draw the play icon
        elif display_mode == 1:
            current_volume = current_volume + 1
            if current_volume > 19:
                current_volume = 19
            else:
                image.paste(vol_list[current_volume], (0,0))  # use now playing image
                # call volume api here (current_volume * 5)

        disp.image(image)

def wheel_left(channel):
    #
    # Wheel turned left (<)
    #
    #global counter, step, wav_pointer, ICON_FONT, image, draw, disp, current_volume
    global noise_pointer, current_volume

    clkState = GPIO.input(18)
    dtState = GPIO.input(17)

    if clkState == 1 and dtState == 0:
        print("Wheel turned left.")
        if display_mode == 0:
            noise_pointer = noise_pointer - 1
            if noise_pointer < 0:
                noise_pointer = len(img_list) - 1
            image.paste(img_list[noise_pointer], (0,0))  # use now playing image
            #print("Now playing: {0}, wav_list.index(now_playing): {1}".format(now_playing, wav_list.index(now_playing)))
            draw.text((1, 110), "\U000F04D5", font=ICON_FONT, fill=(255, 255, 255),)  # draw the play icon
        elif display_mode == 1:
            current_volume = current_volume - 1
            if current_volume < 0:
                current_volume = 0
            else:
                image.paste(vol_list[current_volume], (0,0))  # use now playing image
                # call volume api here (current_volume * 5)

        disp.image(image)

#
#     %%%%%%%%%%%%  Initial program flow continues here %%%%%%
#

# Set button inputs
# stop
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(5, GPIO.RISING, callback=button_stop, bouncetime=DEBOUNCE)

#display
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(21, GPIO.RISING, callback=button_display, bouncetime=DEBOUNCE+100)

# preset 1
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(6, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 2
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(13, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 3
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(19, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

#preset 4
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(26, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# rotary click
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(20, GPIO.RISING, callback=button_rotary_click, bouncetime=DEBOUNCE)

# Set rotary inputs
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(18, GPIO.FALLING, callback=wheel_right, bouncetime=250)

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(17, GPIO.FALLING, callback=wheel_left, bouncetime=250)


# set initial display states
init_controller()

# Get the initial rotary states
# See https://blog.sharedove.com/adisjugo/index.php/2020/05/10/using-ky-040-rotary-encoder-on-raspberry-pi-to-control-volume/
counter = 0
clkLastState = GPIO.input(18)
dtLastState = GPIO.input(17)
swLastState = GPIO.input(20)
step = 1


while True:
    print(display_mode)

    time.sleep(2)
