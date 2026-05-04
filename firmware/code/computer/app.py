import base64
import json

from flask import Flask, jsonify, request
import serial

OS = "windows"  # Change to "linux" or "mac" as needed
COM_NUM = 6  # leave this as None if not on windows
LINUX_AND_MAC_PORT = "/dev/ttyUSB0"  # Change as needed for Linux/Mac
BAUD_RATE = 9600
DISPLAY_WIDTH = 256
DISPLAY_HEIGHT = 64
DISPLAY_PIXELS = DISPLAY_WIDTH * DISPLAY_HEIGHT

serial_string = LINUX_AND_MAC_PORT if OS in ["linux", "mac"] else f"COM{COM_NUM}"

app = Flask(__name__)
ser = serial.Serial(serial_string, BAUD_RATE, timeout=1, write_timeout=1)


def double_check_payload(data, type_):

    if type_ in ["key_func_change", "encoder_func_change"]:

        key_func_change_required_fields = ["executable_type", "executable"]

        if type_ == "key_func_change":

            key_func_change_required_fields.append("key_num")

        else:

            key_func_change_required_fields.append("encoder_action")

        for field in key_func_change_required_fields:

            if field not in data:

                raise ValueError(
                    f"Missing required field '{field}' for function change."
                )

        if data["executable_type"] not in [
            "string",
            "key",
            "key_combo",
            "consumer_control",
        ]:

            raise ValueError("Invalid executable_type.")

        if (
            data["executable_type"] in ["key", "key_combo"]
            and "key_stroke_type" not in data
        ):

            raise ValueError("Missing required field 'key_stroke_type' for key action.")

        if (
            data["executable_type"] == "consumer_control"
            and "consumer_control_type" not in data
        ):

            raise ValueError(
                "Missing required field 'consumer_control_type' for consumer control action."
            )

        if type_ == "encoder_func_change" and data["encoder_action"] not in [
            "clockwise",
            "counterclockwise",
            "button",
        ]:

            raise ValueError("Invalid encoder_action.")

    elif type_ == "display_change":

        if "pixels" not in data:

            raise ValueError("Missing required field 'pixels' for display change.")

        if len(data["pixels"]) != DISPLAY_PIXELS:

            raise ValueError("Display change must include exactly 16384 pixels.")

    else:

        raise ValueError("Unknown message type.")

    return True


def pack_pixels(pixels):

    packed = bytearray(DISPLAY_PIXELS // 8)

    for i, pixel in enumerate(pixels):

        if pixel:

            packed[i // 8] |= 1 << (7 - (i % 8))

    return base64.b64encode(packed).decode("ascii")


def build_serial_payload(payload):

    double_check_payload(payload, payload.get("type", ""))
    serial_payload = dict(payload)

    if serial_payload["type"] == "display_change":

        serial_payload["encoding"] = "1bpp_base64"
        serial_payload["pixels"] = pack_pixels(serial_payload["pixels"])

    return serial_payload


def send_serial_payload(payload):

    serial_payload = build_serial_payload(payload)
    message = json.dumps(serial_payload, separators=(",", ":")).encode("utf-8") + b"\n"
    ser.write(message)
    ser.flush()

    return message


def require_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


@app.errorhandler(ValueError)
def handle_value_error(error):
    return jsonify({"status": "error", "error": str(error)}), 400


@app.route("/")
def index():

    return jsonify({"message": "MORPH serial bridge is running."})


@app.route("/messages/send", methods=["POST"])
def send_data():
    data = require_json_body()
    data.setdefault("type", "key_func_change")

    if data["type"] != "key_func_change":
        raise ValueError("Keyboard messages must use type 'key_func_change'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/messages/send/<int:key_num>", methods=["POST"])
def send_message(key_num):
    data = require_json_body()
    data["key_num"] = key_num
    data.setdefault("type", "key_func_change")

    if data["type"] != "key_func_change":
        raise ValueError("Keyboard messages must use type 'key_func_change'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/messages/send/<int:key_num>/<executable_type>", methods=["POST"])
def send_message_type(key_num, executable_type):
    data = require_json_body()
    data["key_num"] = key_num
    data["executable_type"] = executable_type
    data.setdefault("type", "key_func_change")

    if data["type"] != "key_func_change":
        raise ValueError("Keyboard messages must use type 'key_func_change'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/encoder/send", methods=["POST"])
def send_encoder_data():
    data = require_json_body()
    data.setdefault("type", "encoder_func_change")

    if data["type"] != "encoder_func_change":
        raise ValueError("Encoder messages must use type 'encoder_func_change'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/encoder/send/<encoder_action>", methods=["POST"])
def send_encoder_message(encoder_action):
    data = require_json_body()
    data["encoder_action"] = encoder_action
    data.setdefault("type", "encoder_func_change")

    if data["type"] != "encoder_func_change":
        raise ValueError("Encoder messages must use type 'encoder_func_change'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/oled/send", methods=["POST"])
def send_oled():
    data = require_json_body()
    data.setdefault("type", "display_change")

    if data["type"] != "display_change":
        raise ValueError("OLED messages must use type 'display_change'.")
    if "pixels" not in data:
        raise ValueError("OLED messages must include 'pixels'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


@app.route("/oled/send/default", methods=["POST"])
def send_oled_default():
    data = require_json_body()
    data["type"] = "display_change"

    if "pixels" not in data:
        raise ValueError("OLED messages must include 'pixels'.")

    send_serial_payload(data)
    return jsonify({"status": "sent", "payload": data})


if __name__ == "__main__":
    app.run(debug=True)
