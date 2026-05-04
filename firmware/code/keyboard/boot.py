import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import keypad
import board
import digital_io
import usb_cdc

usb_cdc.enable(console=True, data=True) # USB Serial - to communicate
