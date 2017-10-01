#!/usr/bin/python3

import os
import sys
import time
import datetime
import json
import argparse
import logging
import daemon
import pprint
import subprocess
from math import sin, radians
from daemon import pidfile
import netifaces
import psutil
import pdb

# Adafruit Libraries
from neopixel import *

# OLED Support
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


# SK6812 LED strip configuration:
LED_COUNT      = 3       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0
LED_STRIP      = ws.SK6812_STRIP_RGBW
LED_STATEFILE  = '/var/www/led.json'    # Where LED settings are kept.

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)

debug_p = False

# 128x64 OLED Display 
RST = None
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

def gamma(color8):
    # Gamma color correction for human eye.
    # (from adafruit website).
    gamma = (
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
    1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
    2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
    5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
    10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
    17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
    25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
    37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
    51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
    69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
    90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
    115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
    144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
    177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
    215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 );

    return (gamma[color8])

def show_leds(lednum, red, green, blue, white = 0):

    strip.setPixelColor(int(lednum), Color(gamma(int(green)),  \
                                           gamma(int(red)),\
                                           gamma(int(blue)), \
                                                 int(white)))
    strip.show()

def read_led_statefile():

    leds = {}
    with open(LED_STATEFILE, 'r') as fh:
        leds = json.load(fh)

    # Set initial RGB values that will be used in this daemon,
    # separate from file rgb values
    #pdb.set_trace()
    for lednum in leds['LEDS'].keys():
        leds['LEDS'][lednum]['R'] = leds['LEDS'][lednum]['red']
        leds['LEDS'][lednum]['G'] = leds['LEDS'][lednum]['green']
        leds['LEDS'][lednum]['B'] = leds['LEDS'][lednum]['blue']
        leds['LEDS'][lednum]['W'] = leds['LEDS'][lednum]['white']
    return leds

def do_something():

    epoch_time = time.time()
    st = datetime.datetime.fromtimestamp(epoch_time).strftime('%m/%d/%Y %H:%M:%S')
    print("{}: Starting LED daemon.".format(st))
    # Read SK6812 LED settings.
    leds = read_led_statefile()

    # Create NeoPixel object with appropriate configuration.
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print('Press Ctrl-C to quit.')
    time_now = time_last = time.time()

    red_max   = 0
    green_max = 0
    blue_max  = 0
    white_max = 0
    time_reload_cfg = 60
    while True:
        time_now = time.time()
        if (time_now - time_last) > time_reload_cfg:
            # time to reload the LED config from the statefile.
            leds = read_led_statefile()
            time_last = time_now
            st = datetime.datetime.fromtimestamp(time_now).strftime('%m/%d/%Y %H:%M:%S')
            print("{}: Reloading configuration for LED daemon.".format(st))

        for i in range(0, strip.numPixels()):
            i = str(i)
            if leds['LEDS'][i]['mode'] == 'pwm-sine':
                red_max   = leds['LEDS'][i]['red']
                green_max = leds['LEDS'][i]['green']
                blue_max  = leds['LEDS'][i]['blue']
                white_max = leds['LEDS'][i]['white']
                # PWM sinusoidal 'pulsing' Mode for LEDs
                if 'angle' not in leds['LEDS'][i]:
                    leds['LEDS'][i]['angle'] = 0;
                leds['LEDS'][i]['R'] = abs(sin(radians(leds['LEDS'][i]['angle']))) * red_max
                leds['LEDS'][i]['G'] = abs(sin(radians(leds['LEDS'][i]['angle']))) * green_max
                leds['LEDS'][i]['B'] = abs(sin(radians(leds['LEDS'][i]['angle']))) * blue_max
                leds['LEDS'][i]['W'] = abs(sin(radians(leds['LEDS'][i]['angle']))) * white_max
                leds['LEDS'][i]['angle'] = leds['LEDS'][i]['angle'] + 1.4
                if leds['LEDS'][i]['angle'] > 360:
                    leds['LEDS'][i]['angle'] = 0
            try:
                #print("LED {}: R [{}] G [{}] B [{}] W [{}].".format( i, \
                #           int(leds['LEDS'][i]['R']), int(leds['LEDS'][i]['G']), \
                #           int(leds['LEDS'][i]['B']), int(leds['LEDS'][i]['W'])))
                #pdb.set_trace()
                show_leds(i, leds['LEDS'][i]['R'], leds['LEDS'][i]['G'], \
                             leds['LEDS'][i]['B'], leds['LEDS'][i]['W'])
            except Exception as e:
                print(e.message, e.args)
            time.sleep(0.005)   # 500 microsecond delay

# Main program logic follows:
if __name__ == '__main__':

    do_something()
