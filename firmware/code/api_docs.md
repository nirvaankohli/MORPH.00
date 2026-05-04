# API Docs

## Setup

To start, make sure you have the latest version of pip & python.

Then go into in an editor and edit `app.py`'s `OS` to your OS(windows, linux, or mac).

Depending on your os change either `LINUX_AND_MAC_PORT`(linux or mac) or `COM_NUM`(windows) to what port your macropad is connected to.

Once you have made sure of that run the following commands:

```bash

cd morph.00/code/computer
pip install -r requirements.txt
python app.py

```

The app should be up and running. You should get text in your terminal like(will change a little bit depending on your device):

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with watchdog (windowsapi)
 * Debugger is active!
 * Debugger PIN: 116-642-025

```

To ensure the app is working get the first endpoint:

```text
GET /
```

or just run this:

`curl http://127.0.0.1:5000/`

If all is well you should get something like:

`{"message": "MORPH serial bridge is running."}`

## Keys

Below are the endpoints to change key functions.

```text
POST /messages/send
POST /messages/send/<key_num>
POST /messages/send/<key_num>/<executable_type>
```

* `POST /messages/send`
  * The payload needs to contain:
    * `type: "key_func_change"` - needs to be set to this if you want to change a key_function - can also be not be there and the app will handle the rest
    * `key_num` - The key number you want to change. Goes from 0 to 5 - order is left to right as the key number increases.
    * `executable_type` - what you want the key's function be
      * `string` - types a string
      * `key` - presses key
      * `key_combo` - presses key_combo
      * `consumer_control` - look at `adafruit_hid.consumer_control` dpcs for more info
    *  `executable`
       *   The executable itself - refer to each type's code to figure out what this should be
   * Other optional functions are available
* `POST /messages/send/<key_num>`
  * Same thing as `POST /messages/send` but `key_num` is specified in request url instead of in the payload
* `POST /messages/send/<key_num>/<executable_type>`
  * Same thing as `POST /messages/send` but `key_num` and `executable_type` is specified in request url instead of in the payload

## Rotary Encoder

```text
POST /encoder/send
POST /encoder/send/<encoder_action>
```

* `POST /encoder/send` 
  * The payload needs to contain:
    * `type: encoder_func_change`- needs to be set to this if you want to change a encoder_function - can also be not be there and the app will handle the rest
    * `encoder_action` 
      * `clockwise`- if clockwise movement affects the value
      * `counterclockwise` - if counterclockwise movement affects the value
      * `button` - use it as a button
    * `executable_type`
      * `string` - types a string
      * `key` - presses key
      * `key_combo` - presses key_combo
      * `consumer_control` - look at `adafruit_hid.consumer_control` dpcs for more info
    * `executable`
      * The executable itself - refer to each type's code to figure out what this should
* `POST /encoder/send/<encoder_action>` 
  * Same thing as `POST /encoder/send` but the `encoder_action` is specified in the request url
## OLED

```text
POST /oled/send
POST /oled/send/default
```

* `POST /oled/send` 
  * The payload needs to contain:
    * `type: display_change`- needs to be set to this if you want to change the display - can also be not be there and the app will handle the rest
    * `pixels` - the pixels you want to set the OLED to
* `POST /oled/send/default`
  * Same thing idk why I created a whole new endpoint