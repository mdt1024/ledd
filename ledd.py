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
from math import sin, radians
from daemon import pidfile
from neopixel import *
import pdb


# SK6812 LED strip configuration:
LED_COUNT      = 5       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0
LED_STRIP      = ws.SK6812_STRIP_RGBW
LED_STATEFILE  = '/var/www/led.json'    # Where LED settings are kept.

debug_p = False

def read_led_statefile():

    leds = {}
    with open(LED_STATEFILE, 'r') as fh:
        leds = json.load(fh)

    # Set initial rgb values that will be used in this daemon,
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
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print('Press Ctrl-C to quit.')
    time_now = time_last = time.time()

    red_max   = 0
    green_max = 0
    blue_max  = 0
    white_max = 0
    time_reload_cfg = 300
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
                strip.setPixelColor(int(i), Color(int(leds['LEDS'][i]['G']), \
                                                  int(leds['LEDS'][i]['R']), \
                                                  int(leds['LEDS'][i]['B']), \
                                                  int(leds['LEDS'][i]['W'])))
                strip.show()
            except Exception as e:
                print(e.message, e.args)
            time.sleep(0.005)   # 500 microsecond delay

# Main program logic follows:
if __name__ == '__main__':

    do_something()
