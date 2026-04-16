# Code Report

This report reviews the current state of the code in `code/computer` and `code/keyboard`.

## Files Reviewed

- `code/computer/app.py`
- `code/keyboard/code.py`
- `code/keyboard/boot.py`

## Current Status

The current files parse as valid Python. The earlier protocol and runtime issues have been fixed in the current code:

- Serial messages are newline-delimited and buffered before parsing.
- OLED pixel payloads are packed into `1bpp_base64` before serial transmission.
- OLED pixel counts are validated on both sides.
- The keyboard loop catches malformed JSON or invalid payloads.
- The keyboard loop decodes each JSON message once and dispatches by `type`.
- Keyboard-action payloads require `key_stroke_type` when needed.
- Unknown message types are rejected by the computer-side validator.
- `key_combo_separate` is accepted, with fallback support for the older `key_combo_seperate` spelling.
- `send_serial_payload` now always builds and returns a defined message.

## Current Serial Protocol

Keyboard-action messages are sent as newline-delimited JSON.

OLED messages are accepted by the computer API as full-screen pixel arrays with `16,384` values. Before writing to serial, the computer packs those values into one bit per pixel:

```python
serial_payload["encoding"] = "1bpp_base64"
serial_payload["pixels"] = pack_pixels(serial_payload["pixels"])
```

The keyboard expands that compact payload before drawing:

```python
raw_pixels = binascii.a2b_base64(readable["pixels"].encode("ascii"))
```

A full `256 x 64` OLED frame is now about `2732` base64 characters on the serial wire instead of a JSON array containing `16,384` numbers.

## Remaining Limitations

The OLED packing format is currently binary only. This matches the current `displayio.Bitmap(width, height, 2)` setup. If grayscale output is needed later, the protocol should change from `1bpp_base64` to a multi-bit packed format.

The serial baud rate is still `9600`. The packed OLED payload is much smaller than before, but full-screen updates may still be slow compared with a higher baud rate or smaller region-based updates.

## Verification

The following files parse successfully with Python AST parsing:

- `code/computer/app.py`
- `code/keyboard/code.py`
- `code/keyboard/boot.py`

A local pack/unpack check confirmed that a `256 x 64` frame round-trips correctly and produces a `2732` character base64 payload.
