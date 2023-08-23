# Minimal MicroPython ST7735 Driver Module

A minimal MicroPython driver module for ST7735 TFT SPI display that can blit bytearray and nothing more.

Based from [Boochow's ST7735 Driver](https://github.com/boochow/MicroPython-ST7735) derived from [Guy Carver's Original ST7735 Driver](https://github.com/GuyCarver/MicroPython/blob/master/lib/ST7735.py)

## Features

+ Blit RGB565 bytearray (optionally from FrameBuffer) to display.

+ Initialize ST7735 TFT SPI display driver with rotation, RGB/BGR, and color inversion.

+ Red and green tab is supported (WIP).

## Usage Example

```python
from framebuf import FrameBuffer, RGB565
from machine import Pin, SPI

from ST7735 import TFT

w = 128
h = 160

tft=TFT(
  SPI(
    1,
    baudrate=2 * 10_000_000,
    sck=Pin(18),
    mosi=Pin(23),
  ),
  dc=Pin(12),
  rst=Pin(13),
  cs=Pin(14),
  w=w,
  h=h,
)
tft.init("R") # "R" or "G"
tft.rotation = 0 # 0=up, 1=left, 2=down, 3=right
tft.is_rgb = True # True=RGB, False=BGR

ba = bytearray(w * h * 2)
fb = FrameBuffer(ba, w, h, RGB565)

fb.fill(0xFFFF)
fb.text("Hi, all!", 32, 64, 0x0000)

tft.blit(0, 0, w, h, ba) # Blit
```

## TODO

+ Better initialization support for other tab type
+ Implement RussHughes dynamic initialization

## License

This project is provided under the [GPLv3+ License](https://spdx.org/licenses/GPL-3.0-or-later.html). Feel free to use, modify, and distribute it according to the terms of the license.

