# ST7735 TFT SPI Display Driver
# Translated From ST7735 Sample Code By Guy Carver
# Modified For MicroPython ESP32 By Boochow
# Stripped by CatMeowByte

# SPDX-License-Identifier: GPL-3.0-or-later

from machine import Pin
from time import sleep_us
from math import sqrt

# TFTRotations and TFTRGB are bits to set
# on MADCTL to control display rotation/color layout.
# Looking at display with pins on top.
# 00 = upper left printing right
# 10 = does nothing (MADCTL_ML)
# 20 = upper left printing down (backwards) (Vertical flip)
# 40 = upper right printing left (backwards) (X Flip)
# 80 = lower left printing right (backwards) (Y Flip)
# 04 = (MADCTL_MH)

# 60 = 90 right rotation
# C0 = 180 right rotation
# A0 = 270 right rotation

TFTRotations = [0x00, 0x60, 0xC0, 0xA0]
TFTRGB = 0x00
TFTBGR = 0x08

def clamp(v, l, h):
 return max(l, min(h, v))

ScreenSize = (128, 160)

class TFT(object):
 """SST7735 TFT SPI display driver."""

 NOP = 0x0
 SWRESET = 0x01
 RDDID = 0x04
 RDDST = 0x09

 SLPIN = 0x10
 SLPOUT = 0x11
 PTLON = 0x12
 NORON = 0x13

 INVOFF = 0x20
 INVON = 0x21
 DISPOFF = 0x28
 DISPON = 0x29
 CASET = 0x2A
 RASET = 0x2B
 RAMWR = 0x2C
 RAMRD = 0x2E

 VSCRDEF = 0x33
 VSCSAD = 0x37

 COLMOD = 0x3A
 MADCTL = 0x36

 FRMCTR1 = 0xB1
 FRMCTR2 = 0xB2
 FRMCTR3 = 0xB3
 INVCTR = 0xB4
 DISSET5 = 0xB6

 PWCTR1 = 0xC0
 PWCTR2 = 0xC1
 PWCTR3 = 0xC2
 PWCTR4 = 0xC3
 PWCTR5 = 0xC4
 VMCTR1 = 0xC5

 RDID1 = 0xDA
 RDID2 = 0xDB
 RDID3 = 0xDC
 RDID4 = 0xDD

 PWCTR6 = 0xFC

 GMCTRP1 = 0xE0
 GMCTRN1 = 0xE1

 def __init__(self, mSPI, dc, rst, cs, w=128, h=160, rotation=0, is_rgb=True):
  """Initialize SST7735 TFT SPI display driver."""
  self.w = w
  self.h = h
  self._rotation = rotation # Vertical with top toward pins
  self._is_rgb = is_rgb # Color order

  self.tfa = 0 # Top fixed area
  self.bfa = 0 # Bottom fixed area

  self.spi = mSPI

  self.dc = dc
  self.reset = rst
  self.cs = cs

  self.dc.init(mode=Pin.OUT, pull=Pin.PULL_DOWN)
  self.reset.init(mode=Pin.OUT, pull=Pin.PULL_DOWN)
  self.cs.init(mode=Pin.OUT, pull=Pin.PULL_DOWN)
  self.cs(1)

  self.offset = bytearray(2)
  self.window = bytearray(4)

 def on(self, on=True):
  """Turn display on or off."""
  self._CMD(TFT.DISPON if on else TFT.DISPOFF)

 def invert(self, inv):
  """Invert the color data."""
  self._CMD(TFT.INVON if inv else TFT.INVOFF)

 @property
 def is_rgb(self):
   """Get RGB or BGR color order."""
   return self._is_rgb

 @is_rgb.setter
 def is_rgb(self, value):
  """Toggle RGB or BGR color order."""
  self._is_rgb = value
  self._MADCTL()

 @property
 def rotation(self):
   """Get rotation (0-3)."""
   return self._rotation

 @rotation.setter
 def rotation(self, value):
  """Set rotation (0-3). Starts vertical with top toward pins and rotates 90 deg
    clockwise each step."""
  if (0 <= value < 4):
   rot = self._rotation ^ value
   self._rotation = value

   # If switching from vertical to horizontal swap x and y
   # (indicated by bit 0 changing)
   if (rot & 1):
    self.w, self.h = self.h, self.w

   self._MADCTL()

 def blit(self, x0, y0, x1, y1, data):
  self._WINDOW(x0, y0, x1, y1)
  self._DATA(data)

 # @micropython.native
 def _WINDOW(self, x0, y0, x1, y1):
  """Set the rectangular area for drawing data."""
  self._CMD(TFT.CASET) # Column address set
  self.window[0] = self.offset[0]
  self.window[1] = self.offset[0] + int(x0)
  self.window[2] = self.offset[0]
  self.window[3] = self.offset[0] + int(x1)
  self._DATA(self.window)

  self._CMD(TFT.RASET) # Row address set
  self.window[0] = self.offset[1]
  self.window[1] = self.offset[1] + int(y0)
  self.window[2] = self.offset[1]
  self.window[3] = self.offset[1] + int(y1)
  self._DATA(self.window)

  self._CMD(TFT.RAMWR) # Write to RAM

 def _CMD(self, cmd):
  """Write command to the device."""
  self.dc(0)
  self.cs(0)
  self.spi.write(bytearray([cmd]))
  self.cs(1)

 def _DATA(self, data):
  """Write data to the device."""
  self.dc(1)
  self.cs(0)
  self.spi.write(data)
  self.cs(1)

 def _MADCTL(self):
  """Set screen rotation and RGB/BGR order."""
  self._CMD(TFT.MADCTL)
  self._DATA(bytearray([TFTRotations[self._rotation] | (TFTRGB if self._is_rgb else TFTBGR)]))

 def _RESET(self):
  """Reset the device."""
  self.dc(0)
  self.reset(1)
  sleep_us(500)
  self.reset(0)
  sleep_us(500)
  self.reset(1)
  sleep_us(500)

 def init(self, tab):
  """Initialize based on tab color (R,G)."""

  # Early bail
  if tab not in ["R", "G"]:
   return

  self._RESET()

  self._CMD(TFT.SWRESET)       # Software reset
  sleep_us(150)
  self._CMD(TFT.SLPOUT)        # Out of sleep mode

  if tab == "R":
   sleep_us(500)
  if tab == "G":
   sleep_us(255)

  d1 = bytearray(1)
  d2 = bytearray(2)
  d3 = bytearray(3)
  d6 = bytearray(6)
  d16 = bytearray(16)

  d3 = bytearray([0x01, 0x2C, 0x2D]) # Fastest refresh, 6 lines front, 3 lines back
  self._CMD(TFT.FRMCTR1) # Frame rate control
  self._DATA(d3)

  self._CMD(TFT.FRMCTR2) # Frame rate control
  self._DATA(d3)

  d6 = bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d])
  self._CMD(TFT.FRMCTR3) # Frame rate control
  self._DATA(d6)
  sleep_us(10)

  self._CMD(TFT.INVCTR) # Display inversion control
  d1[0] = 0x07 # Line inversion
  self._DATA(d1)

  self._CMD(TFT.PWCTR1) # Power control
  d3[0] = 0xA2
  d3[1] = 0x02
  d3[2] = 0x84
  self._DATA(d3)

  self._CMD(TFT.PWCTR2) #Power control
  d1[0] = 0xC5 # VGH = 14.7V, VGL = -7.35V
  self._DATA(d1)

  self._CMD(TFT.PWCTR3) # Power control
  d2[0] = 0x0A # Opamp current small
  d2[1] = 0x00 # Boost frequency
  self._DATA(d2)

  self._CMD(TFT.PWCTR4) # Power control
  d2[0] = 0x8A # Opamp current small
  d2[1] = 0x2A # Boost frequency
  self._DATA(d2)

  self._CMD(TFT.PWCTR5) # Power control
  d2[0] = 0x8A # Opamp current small
  d2[1] = 0xEE # Boost frequency
  self._DATA(d2)

  self._CMD(TFT.VMCTR1) # Power control
  d1[0] = 0x0E
  self._DATA(d1)

  self._CMD(TFT.INVOFF)

  self._CMD(TFT.MADCTL) # Power control

  if tab == "R":
   d1[0] = 0xC8
   self._DATA(d1)

  self._CMD(TFT.COLMOD)
  d1[0] = 0x05
  self._DATA(d1)

  self._CMD(TFT.CASET) # Column address set
  self.window[0] = 0x00

  if tab == "R":
   self.window[1] = 0x00
  if tab == "G":
   self.window[1] = 0x01 # Starts at row/column 1

  self.window[2] = 0x00
  self.window[3] = self.w - 1
  self._DATA(self.window)

  self._CMD(TFT.RASET) # Row address set
  self.window[3] = self.h - 1
  self._DATA(self.window)

  if tab == "R":
   d16 = bytearray([
    0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22,
    0x1f, 0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10
   ])
  if tab == "G":
   d16 = bytearray([
    0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d,
    0x29, 0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10
   ])

  self._CMD(TFT.GMCTRP1)
  self._DATA(d16)

  if tab == "R":
   d16 = bytearray([
    0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e,
    0x30, 0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10
   ])
  if tab == "G":
   d16 = bytearray([
    0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d,
    0x2e, 0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10
   ])

  self._CMD(TFT.GMCTRN1)
  self._DATA(d16)

  if tab == "G":
   self._CMD(TFT.NORON) # Normal display on

  sleep_us(10)

  self._CMD(TFT.DISPON)
  sleep_us(100)

  if tab == "R":
   self._CMD(TFT.NORON) # Normal display on
   sleep_us(10)

  self.cs(1)