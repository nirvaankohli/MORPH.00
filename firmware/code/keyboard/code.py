import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

import keypad

import board
import busio
import digital_io
import rotaryio
import usb_cdc

import json
import binascii
import time

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

import displayio
import fourwire
from adafruit_ssd1322 import SSD1322



# Set Up/Configuration

oled_pins = {}
(
    oled_pins["sck"],
    oled_pins["mosi"],
    oled_pins["cs"],
    oled_pins["dc"],
    oled_pins["rst"],

) = (board.SCK, board.MOSI, board.A2, board.A0, board.A1)

spi = busio.SPI(oled_pins["sck"], oled_pins["mosi"])

cs = digital_io.DigitalInOut(oled_pins["cs"])
dc = digital_io.DigitalInOut(oled_pins["dc"])
rst = digital_io.DigitalInOut(oled_pins["rst"])

display_bus = fourwire.FourWire(
    spi, command=dc, chip_select=cs, reset=rst, baudrate=1000000
)

display = SSD1322(display_bus, width=256, height=64)

kbd = Keyboard(usb_hid.devices)  # set keyboard object
cc = ConsumerControl(usb_hid.devices)
serial = usb_cdc.data  # setting up the desktop and macropad communication
layout = KeyboardLayoutUS(kbd)

key_mapping = {
    0: [6, board.D2, None],
    1: [7, board.D3, None],
    2: [8, board.D4, None],
    3: [9, board.D5, None],
    4: [10, board.D6, None],
    5: [11, board.D8, None],
}  # mapping of key - key_num : [key_pin_num, board.pin, function]

encoder_pins = {
    "a": board.D7,
    "b": board.D9,
    "button": board.D10,
}

encoder_mapping = {
    "clockwise": None,
    "counterclockwise": None,
    "button": None,
}


# init keys - use dictionary

keys = keypad.Keys(
    tuple(key_mapping[i][1] for i in key_mapping), value_when_pressed=False, pull=True
)

encoder = rotaryio.IncrementalEncoder(encoder_pins["a"], encoder_pins["b"])
encoder_button = keypad.Keys((encoder_pins["button"],), value_when_pressed=False, pull=True)


class keyboard_action:

    def __init__(self, json_load):

        self.json_load = json_load

        self.executable_type = json_load["executable_type"]
        self.executable_type_options = ["string", "key", "key_combo", "consumer_control"]

        self.key_num = json_load.get("key_num")
        self.encoder_action = json_load.get("encoder_action")

        try:
            self.press = (
                True
                if json_load.get("kbd_press_or_send", json_load.get("press_or_send"))
                == "press"
                else False
            )
        except AttributeError:
            self.press = False

        if self.executable_type not in self.executable_type_options:

            raise ValueError(
                f"Invalid executable type: {self.executable_type}. Must be one of {self.executable_type_options}."
            )

        self.executable = self.get_executable_value()

        if self.executable_type == "consumer_control":

            self.executable_function = cc.send
            self.press_hold = []

        elif self.press:

            self.executable_function = kbd.press

            try:

                self.press_hold = json_load["kbd_press_hold"]

                if not isinstance(self.press_hold, list):

                    self.press_hold = [self.press_hold]

            except KeyError:

                self.press_hold = [1.0]

        else:

            self.executable_function = kbd.send
            self.press_hold = []

        if self.executable_type == "key_combo":

            try:

                if "key_combo_separate" in json_load:

                    self.key_combo_seperate = json_load["key_combo_separate"]

                else:

                    self.key_combo_seperate = json_load["key_combo_seperate"]

            except KeyError:

                self.key_combo_seperate = len(self.press_hold) > 1

    def get_executable_value(self):

        executable = self.json_load["executable"]

        if self.executable_type == "string":

            return executable

        if self.executable_type == "consumer_control":

            consumer_control_type = self.json_load["consumer_control_type"]

            if consumer_control_type == "int":

                return executable

            if consumer_control_type == "ConsumerControlCode":

                return (
                    getattr(ConsumerControlCode, executable)
                    if isinstance(executable, str)
                    else executable
                )

            raise ValueError(
                "Invalid consumer control type. Must be 'int' or 'ConsumerControlCode'."
            )

        key_stroke_type = self.json_load["key_stroke_type"]

        if key_stroke_type == "int":

            return executable

        if key_stroke_type == "Keycode":

            if self.executable_type == "key_combo":

                return [
                    getattr(Keycode, key) if isinstance(key, str) else key
                    for key in executable
                ]

            return (
                getattr(Keycode, executable)
                if isinstance(executable, str)
                else executable
            )

        raise ValueError(
            f"Invalid key stroke type: {key_stroke_type}. Must be 'int' or 'Keycode' for key presses."
        )

    def get_press_hold(self, index=0):

        if not self.press_hold:

            return 0

        if index < len(self.press_hold):

            return self.press_hold[index]

        return self.press_hold[0]

    def execute(self):

        # execute the action based on the type of action

        if self.executable_type == "string":

            layout.write(self.executable)

        elif self.executable_type == "key":

            if self.press:

                self.executable_function(self.executable)

                if self.press_hold:

                    time.sleep(self.get_press_hold())

                    kbd.release(self.executable)

            else:

                self.executable_function(self.executable)

        elif self.executable_type == "key_combo":

            if self.press:

                if self.key_combo_seperate:

                    for i, key in enumerate(self.executable):

                        self.executable_function(key)

                        if self.press_hold:

                            time.sleep(self.get_press_hold(i))

                            kbd.release(key)

                else:

                    self.executable_function(*self.executable)

                    if self.press_hold:

                        time.sleep(self.get_press_hold())

                        kbd.release(*self.executable)

            else:

                if self.key_combo_seperate:

                    for key in self.executable:

                        self.executable_function(key)

                else:

                    self.executable_function(*self.executable)

        elif self.executable_type == "consumer_control":

            self.executable_function(self.executable)

        return True


def array_to_display_io_bitmap(array, width, height):

    bitmap = displayio.Bitmap(width, height, 2)

    for y in range(height):

        for x in range(width):

            bitmap[x, y] = array[y * width + x]

    return bitmap


def bitmap_to_display_io_tilegrid(bitmap, width, height):

    palette = displayio.Palette(2)
    palette[0] = 0x000000  # Black
    palette[1] = 0xFFFFFF  # White

    tilegrid = displayio.TileGrid(bitmap, pixel_shader=palette)

    return tilegrid


def unpack_pixels(readable):

    if readable.get("encoding") != "1bpp_base64":

        return readable["pixels"]

    raw_pixels = binascii.a2b_base64(readable["pixels"].encode("ascii"))
    pixels = []

    for byte in raw_pixels:

        for shift in range(7, -1, -1):

            pixels.append((byte >> shift) & 1)

    return pixels[: display.width * display.height]


def decrypt_serial_display_change(readable):

    array_of_pixels = unpack_pixels(readable)

    if len(array_of_pixels) != display.width * display.height:

        raise ValueError("Pixel array length does not match display size.")

    bitmap = array_to_display_io_bitmap(
        array_of_pixels, display.width, display.height
    )

    tile_grid = bitmap_to_display_io_tilegrid(bitmap, display.width, display.height)

    return bitmap, tile_grid


def decrypt_serial_key_change(readable):

    return keyboard_action(readable)


def decrypt_serial_encoder_change(readable):

    return keyboard_action(readable)


def get_key_mapping_index(key_num):

    if key_num in key_mapping:

        return key_num

    for i in key_mapping:

        if key_mapping[i][0] == key_num:

            return i

    return None


def check_if_hold_key(current, old):

    return bool(
        old and current.key_number == old.key_number and current.pressed and old.pressed
    )


# loop

old_key_event = None
last_encoder_position = encoder.position
serial_buffer = b""

while True:

    key_event = keys.events.get()

    if key_event:

        key_number = key_event.key_number
        pressed = key_event.pressed
        hold = check_if_hold_key(key_event, old_key_event)

        try:

            key_func = key_mapping[key_number][2]

        except KeyError:

            key_func = None

        if (not hold) and pressed and key_func:

            success = key_func.execute()

        old_key_event = key_event

    encoder_position = encoder.position

    if encoder_position != last_encoder_position:

        if encoder_position > last_encoder_position:

            encoder_func = encoder_mapping["clockwise"]

        else:

            encoder_func = encoder_mapping["counterclockwise"]

        if encoder_func:

            success = encoder_func.execute()

        last_encoder_position = encoder_position

    encoder_button_event = encoder_button.events.get()

    if encoder_button_event and encoder_button_event.pressed:

        encoder_func = encoder_mapping["button"]

        if encoder_func:

            success = encoder_func.execute()

    if serial is not None and serial.in_waiting > 0:

        serial_buffer += serial.read(serial.in_waiting)

        while b"\n" in serial_buffer:

            data, serial_buffer = serial_buffer.split(b"\n", 1)

            if not data:

                continue

            serial.write(b"Received: " + data + b"\n")

            try:

                readable = json.loads(data.decode("utf-8"))

                if readable.get("type") == "key_func_change":

                    obj = decrypt_serial_key_change(readable)
                    mapping_index = get_key_mapping_index(obj.key_num)

                    if mapping_index is not None:

                        key_mapping[mapping_index][2] = obj

                elif readable.get("type") == "encoder_func_change":

                    obj = decrypt_serial_encoder_change(readable)

                    if obj.encoder_action in encoder_mapping:

                        encoder_mapping[obj.encoder_action] = obj

                elif readable.get("type") == "display_change":

                    bitmap, tile_grid = decrypt_serial_display_change(readable)
                    display.show(tile_grid)

                else:

                    print("Invalid data received:", data)

            except Exception as error:

                print("Invalid data received:", data, error)
