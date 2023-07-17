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
from adafruit_seesaw import seesaw, rotaryio

USE_ROTARY = True
USE_DISPLAY = True

# Adafruit I2C QT Rotary Encoder
# Using the INT output on Pi GPIO 17
try:
    seesaw = seesaw.Seesaw(board.I2C(), addr=0x36)
except:
    print("Error initializing the rotary encoder board.")
    USE_ROTARY = False
else:
    seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
    print("Found seesaw supported product {}".format(seesaw_product))
    if seesaw_product != 4991:
        print("Wrong firmware loaded for QT encoder?  Expected 4991")
    # Set up the rotary click button, and add to interrupt
    seesaw.pin_mode(24, seesaw.INPUT_PULLUP)  # Pin on the QT
    seesaw.set_GPIO_interrupts(1 << 24, True)
    seesaw.enable_encoder_interrupt()

# TFT configuration for CS and DC pins:
cs_pin = digitalio.DigitalInOut(board.CE0) #pin24
dc_pin = digitalio.DigitalInOut(board.D25) #pin22
reset_pin = digitalio.DigitalInOut(board.D24) #pin18

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

try:
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
except:
    print("No display or error setting up display.")
    disp = False
    USE_DISPLAY = False

if USE_DISPLAY:
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

# image for about screen
img_about = Image.new("RGB", (width, height))

# tiny images for fwd/rev wheel icon
img_right = Image.new('RGB', (20, 20), (0, 0, 0))
img_left = Image.new('RGB', (20, 20), (0, 0, 0))

# Drawing object for main display image
draw = ImageDraw.Draw(image)

wav_list = []  # list of available wav files to play (strings)
img_list = []  # list of images to display for each wav file (images)
vol_list = []  # list of volume bars representing volumes (images)
noise_pointer = 0  # index of currently displayed noise image when rotating wheel (int)
rotary_pos = 0  # keeps track of wheel position
now_playing = ""  # name of currently playing file or emply string
display_mode = 0  # int display mode (0-2)
current_volume = 10  # default current volume if none saved (0-20)
new_volume = 10 # variable to see if volume has changed
loop_count = 0  # loop counter for checking the current sound status
IMAGE_PATH = os.getenv('MEDIA_PATH', "/data/my_data/noise/")  # string path to noise and images
ASSET_PATH = os.getenv('ASSET_PATH', "/data/my_data/assets/") # string path to non-noise assets
TEXT_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
ICON_FONT = ImageFont.truetype("/usr/src/app/materialdesignicons-webfont.ttf", 20)
DEBOUNCE = 600  # switch debounce time in ms
rot_first = datetime.datetime.now()
rot_last = datetime.datetime.now()

P1_GPIO = 6
P2_GPIO = 13
P3_GPIO = 12 # was 19
P4_GPIO = 20
DISP_GPIO = 22 # was 21
STOP_GPIO = 5

def lib_setup():
    #
    # Generate list of all sound files available,
    # create list of all images with titles burned in,
    # create volume image list
    # create wheel icon images
    #
    global wav_list, img_list, img_info, img_left, img_right
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
                i = Image.open(ASSET_PATH + "default.jpg")
            save_image.paste(i, (0,0))
            save_image.paste(img_info, (0, 108))
            text = noise_name.replace("_", " ")
            save_draw.text((20, 110), text, font=font, fill=(255, 255, 255),)
            img_list.append(save_image)
    # generate a list of 20 vol images:
    for v in range(0, 21):
        save_image = Image.new("RGB", (width, height))
        save_draw = ImageDraw.Draw(save_image)
        save_draw.rectangle((0, 0, width, height), fill=(0, 0, 0))  # draw black box
        i = Image.open(ASSET_PATH + "vol_" + "{:0>3}".format(v * 5) + ".jpg")
        save_image.paste(i, (0,50))
        text = "volume: " + str(v * 5) + " %"
        save_draw.text((20, 110), text, font=font, fill=(255, 255, 255),)
        save_draw.text((1, 110), "\U000F057F", font=ICON_FONT, fill=(255, 255, 255),)
        vol_list.append(save_image)

    # wheel icon images
    wheel_draw = ImageDraw.Draw(img_left)
    wheel_draw.text((1, 1), "\U000F04D5", font=ICON_FONT, fill=(255, 255, 255),)  # draw the left sel icon
    wheel_draw = ImageDraw.Draw(img_right)
    wheel_draw.text((1, 1), "\U000F04D7", font=ICON_FONT, fill=(255, 255, 255),)  # draw the right sel icon

def create_idle_image():
    #
    # Create the idle image!
    #
    global idle_image
    idle_image_raw = Image.new("RGB", (width, height))
    try:
        idle_image_raw = Image.open(ASSET_PATH + "idle.jpg")
    except:
        # if no idle image found, draw a rectangle instead
        idle_image_draw = ImageDraw.Draw(idle_image_raw)
        idle_image_draw.rectangle((0, 0, width, height), fill=(0, 100, 200))
    idle_image.paste(idle_image_raw, (0,0))  # use idle image
    idle_draw = ImageDraw.Draw(idle_image)
    idle_image.paste(img_info, (0, 108))
    idle_draw.text((1, 110), "\U000F04DB", font=ICON_FONT, fill=(255, 255, 255),)  # draw the stop icon
    #font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    idle_draw.text((20, 110), "(idle)", font=TEXT_FONT, fill=(255, 255, 255),)

# Setup initial state
def init_controller():
    print("init display")
    global disp, image, draw, now_playing, idle_image

    try:
        image = Image.open(ASSET_PATH + "splash.jpg")
    except:
        print("Error accessing splash.jpg - using default splash screen instead.")
        # Draw a blue box for init display
        draw.rectangle((0, 0, width, height), fill=(0, 0, 72))

        # Load a TTF Font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

        # Draw splash screen
        text = "Welcome!"
        draw.text((3, 10), text, font=font, fill=(255, 255, 0),)
    else:
        if USE_DISPLAY:
            disp.image(image)
    time.sleep(1)
    lib_setup()
    time.sleep(1)
    create_idle_image()
    time.sleep(1)
    display_info()

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

def current_status():
    #
    # Calls the noise service and updates display
    #
    # get current status
    r = requests.get('http://noise:5000/')
    j = r.json()
    if j["status"] == "stop":
        if now_playing != "":
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
    global img_about
    draw_about = ImageDraw.Draw(img_about)
    font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    img_about.paste(img_info, (0, 108))
    draw_about.text((22, 110), "device info", font=TEXT_FONT, fill=(255, 255, 255),)
    draw_about.text((1, 110), "\U000F02FD", font=ICON_FONT, fill=(255, 255, 255),)
    # Prep screen to cover "Reading..."
    draw_about.rectangle((0, 0, width, 107), fill=(0, 0, 72))  # draw blue bkgd
    # Use supervisor API to get info
    r = requests.get(os.getenv('BALENA_SUPERVISOR_ADDRESS') + "/v1/device?apikey=" + os.getenv('BALENA_SUPERVISOR_API_KEY'))
    j = r.json()
    draw_about.text((1, 7), "IP:", font=font2, fill=(255, 165, 0),)
    draw_about.text((1, 41), "balenaOS:", font=font2, fill=(255, 165, 0),)
    draw_about.text((1, 75), "REL:", font=font2, fill=(255, 165, 0),)
    draw_about.text((1, 23), j["ip_address"], font=font2, fill=(255, 255, 255),)
    draw_about.text((1, 57), j["os_version"][9:], font=font2, fill=(255, 255, 255),)
    draw_about.text((1, 91), j["commit"][:7], font=font2, fill=(255, 255, 255),)

def button_stop(channel):
    #
    # stop payback
    #
    global now_playing
    r = requests.post('http://noise:5000/stop/')
    print("Stop button pressed.")
    now_playing = ""
    display_now(idle_image)

def button_display(channel):
    #
    # change display mode
    #
    global display_mode, display_timer
    print("pressed display button")
    display_mode = display_mode + 1
    if display_mode == 3:
        display_mode = 0
    # Decide what to display
    if display_mode == 0:
        if now_playing == "":
            display_now(idle_image)
        else:
            display_now(img_list[wav_list.index(now_playing)])
    elif display_mode == 1:
        image.paste(vol_list[current_volume], (0,0))
        if USE_DISPLAY:
            disp.image(image)
    elif display_mode == 2:
        if USE_DISPLAY:
            disp.image(img_about)

def button_preset(channel):
    #
    # play a preset
    #
    # get preset number (1-4) from channel
    preset_channel = [P1_GPIO, P2_GPIO, P3_GPIO, P4_GPIO]
    presety = preset_channel.index(channel)
    # get preset name value from redis
    r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    p = r.get("p" + str(presety + 1))
    print("Preset {0} ({1}) pressed.".format(p, presety))
    # play/display the file image
    if p is None:
        print("No preset value for {}".format(presety))
    else:
        text_icon = ["\U000F03A4", "\U000F03A7", "\U000F03AA", "\U000F03AD"]
        play_file(p, text_icon[presety])

def button_rotary_click():
    #
    # called on rotary click
    #

    global display_mode

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
    if noise_name == '':
        print("Warning! Noise with no name requested.")
        return
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
    
    d_img_draw = ImageDraw.Draw(d_img)
    #image.paste(d_img, (0,0))  # use now playing image
    #print("Now playing: {0}, wav_list.index(now_playing): {1}".format(now_playing, wav_list.index(now_playing)))
    d_img_draw.text((1, 110), "\U000F040A", font=ICON_FONT, fill=(255, 255, 255),)  # draw the play icon
    if len(extra_icon) > 0:   # draw the extra icon
        d_img_draw.text((105, 5), extra_icon, font=ICON_FONT, fill=(255, 255, 255),)

    if USE_DISPLAY:
        disp.image(d_img)

def rotary_incoming(r):
    #
    # Triggered by rotary QT interrupt
    # when rotary wheel is turned or clicked
    #
    global rotary_pos, rot_first, rot_last
    current_pos = seesaw.encoder_position()
    rot_btn = not(seesaw.digital_read(24))
    print("rotary pos: {0}; current_pos: {1}; rot_btn: {2}".format(rotary_pos, current_pos, rot_btn))
    if rotary_pos == current_pos:
        if rot_btn == True:
            print("Button pressed!")
            button_rotary_click()
    else:
        #rot_first = datetime.datetime.now()
        #diff = rot_first - rot_last
        if current_pos < rotary_pos:
            print("Turned right {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                wheel_right()
        else:
            print("Turned left {}".format(current_pos))
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                wheel_left()
        #rot_last = datetime.datetime.now()
        #print("diff: {}".format(diff.microseconds))
    rotary_pos = current_pos
    #print("seesaw rotary data updated! {0}, {1}".format(rot_pos, rot_btn))
    
def wheel_right():
    #
    # Wheel turned right (>)
    #
    
    global disp, noise_pointer, current_volume, image

    if display_mode == 0:
        noise_pointer = noise_pointer + 1
        if noise_pointer > len(img_list) - 1:
            noise_pointer = 0
        image.paste(img_list[noise_pointer], (0,0))
        image.paste(img_right, (1, 110))
        #draw.text((50, 50), "RIGHT", font=TEXT_FONT, fill=(255, 255, 255),)
        #draw.text((1, 110), "\U000F04D7", font=ICON_FONT, fill=(255, 255, 255),)  # draw the right sel icon
    elif display_mode == 1:
        current_volume = current_volume + 1
        if current_volume > 19:
            current_volume = 19
        else:
            image.paste(vol_list[current_volume], (0,0))
    
    if USE_DISPLAY:
        disp.image(image)

def wheel_left():
    #
    # Wheel turned left (<)
    #
 
    global noise_pointer, current_volume, draw

    if display_mode == 0:
        noise_pointer = noise_pointer - 1
        if noise_pointer < 0:
            noise_pointer = len(img_list) - 1
        image.paste(img_list[noise_pointer], (0,0))
        image.paste(img_left, (1, 110))
        draw.text((1, 110), "\U000F04D5", font=ICON_FONT, fill=(255, 255, 255),)  # draw the left sel icon
    elif display_mode == 1:
        current_volume = current_volume - 1
        if current_volume < 0:
            current_volume = 0
        else:
            image.paste(vol_list[current_volume], (0,0))
    if USE_DISPLAY:
        disp.image(image)

#
#     %%%%%%%%%%%%  Initial program flow continues here %%%%%%
#

print("Starting...")

# Set button inputs
# stop
GPIO.setup(STOP_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(STOP_GPIO, GPIO.RISING, callback=button_stop, bouncetime=DEBOUNCE)

#display
GPIO.setup(DISP_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(DISP_GPIO, GPIO.RISING, callback=button_display, bouncetime=DEBOUNCE+200)

# preset 1
GPIO.setup(P1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P1_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 2
GPIO.setup(P2_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P2_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

# preset 3
GPIO.setup(P3_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P3_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

#preset 4
GPIO.setup(P4_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(P4_GPIO, GPIO.RISING, callback=button_preset, bouncetime=DEBOUNCE)

#rotaryio interrupt
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(17, GPIO.FALLING, callback=rotary_incoming)

# set initial display states
init_controller()

# get saved volume, if available
redis_conn = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
v = redis_conn.get("v")
if v is not(None):
    current_volume = int(v)
new_volume = current_volume

while True:
    loop_count = loop_count + 1
    if loop_count == 5:
        loop_count = 0
        #  Check to see if some other process has changed the status
        try:
            r = requests.get('http://noise:5000/')
        except:
            print("Error accessing noise service.")
        j = r.json()
        if j["status"] == "stop":
            if now_playing != "":
                now_playing = ""
                display_now(idle_image)
        else:
            if now_playing != j["file"]:
                now_playing = j["file"]
                display_now(img_list[wav_list.index(now_playing)])
        # See if we need to save a new volume level in Redis
        if current_volume != new_volume:
            # Save volume in Redis
            try:
                redis_conn.set('v', current_volume)
            except:
                print("Error saving volume data to Redis.")
            new_volume = current_volume

    time.sleep(2)
