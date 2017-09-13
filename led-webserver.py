#!/usr/bin/python3

from flask import Flask, request, make_response
import time
import json
import pdb

LED_STATEFILE  = '/var/www/led.json'

app = Flask(__name__)

@app.route('/', methods=["GET"])
def api_root():
    return { "led_url": request.url + "led/(green | red)/",
             "led_url_POST": {"state": "(0 | 1)"}}
  
@app.route('/led/<color>/', methods=["GET", "POST"])
def api_leds_control(color):
    if request.method == "POST":
        if color in LEDS:
            GPIO.output(LEDS[color], int(request.data.get("state")))
    return {color: GPIO.input(LEDS[color])}
 
@app.route('/led/rainbow/', methods=["GET", "POST"])
def api_leds_rainbow():
    rainbow(strip)
    return 1

@app.route('/setled', methods=["GET"])
def api_leds_setled():
    # http://192.168.1.55:12345/setled?led=1&red=255&green=128&blue=0&white=0
    led = request.args.get('led')
    mode = request.args.get('mode')
    red = int(request.args.get('red'))
    green = int(request.args.get('green'))
    blue = int(request.args.get('blue'))
    white = int(request.args.get('white'))
    if not mode:
        mode = 'solid'  # Set default LED mode to 'solid'

    print("Setting LED #{} to color [{}, {}, {}, {}] and mode {}.".format(led, red, green, blue, white, mode))
    # Read existing LED statefile.

    leds = {}
    try:
        with open(LED_STATEFILE, 'r') as fh:
            leds = json.load(fh)
    except json.decoder.JSONDecodeError as e:
        # Assume JSON is bad and overwrite the file with just one LED entry.
        print("File {} has bad JSON: {}.".format(jsonfile, e))
        leds = { 'LEDS': { led: {'mode': mode, 'blue' : blue, 'red': red, 'green': green, 'white': white}}}
    else:
        if led not in leds['LEDS']:
            leds['LEDS'][led] = {'red': red, 'green': green, 'blue': blue, \
                                     'white': white, 'mode': mode }
        else:
            leds['LEDS'][led]['red']   = red
            leds['LEDS'][led]['green'] = green
            leds['LEDS'][led]['blue']  = blue
            leds['LEDS'][led]['white'] = white
            leds['LEDS'][led]['mode']  = mode

    # Write out updated LED statefile.
    with open(LED_STATEFILE, 'w') as fh:
        json.dump(leds, fh)

    return "Set R[{}] G[{}] B[{}] W[{}] for LED {} with mode {}".format(red, green, blue, white, led, mode)

if __name__ == "__main__":

    app.run(host='192.168.1.55', port=12345, debug=True)
