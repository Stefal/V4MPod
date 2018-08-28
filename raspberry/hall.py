import os
import sys
import smbus
import time
import datetime
import RPi.GPIO as GPIO
import PyCmdMessenger
import subprocess
import gpsd
import threading

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
import lcd_menu as menu

from queue import Queue
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

cam_range=0b00001111

# Set Rpi.GPIO to BCM mode
GPIO.setmode(GPIO.BCM)

# Channel used to receive MCP interrupts
mcp1_inta_pin = 19
mcp1_intb_pin = 16
mcp2_inta_pin = 26
mcp2_intb_pin = 20

# Set these channels as input
GPIO.setup(mcp1_inta_pin, GPIO.IN)
GPIO.setup(mcp1_intb_pin, GPIO.IN)
GPIO.setup(mcp2_inta_pin, GPIO.IN)
GPIO.setup(mcp2_intb_pin, GPIO.IN)

#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1
Keypressed = False
MCP1 = 0x21
MCP2 =  0x20 # Device address (A0-A2)
IODIRA =  0x00   # IO direction  (0 = output, 1 = input (Default))
IODIRB =  0x01
IOPOLA =  0x02   # IO polarity   (0 = normal, 1 = inverse)
IOPOLB =  0x03
GPINTENA =0x04   # Interrupt on change (0 = disable, 1 = enable)
GPINTENB =0x05
DEFVALA = 0x06   # Default comparison for interrupt on change (interrupts on opposite)
DEFVALB = 0x07
INTCONA = 0x08   # Interrupt control (0 = interrupt on change from previous, 1 = interrupt on change from DEFVAL)
INTCONB = 0x09
IOCON =   0x0A   # IO Configuration: bank/mirror/seqop/disslw/haen/odr/intpol/notimp
#IOCON 0x0B  // same as 0x0A
GPPUA =   0x0C   # Pull-up resistor (0 = disabled, 1 = enabled)
GPPUB =   0x0D
INFTFA =  0x0E   # Interrupt flag (read only) : (0 = no interrupt, 1 = pin caused interrupt)
INFTFB =  0x0F
INTCAPA = 0x10   # Interrupt capture (read only) : value of GPIO at time of last interrupt
INTCAPB = 0x11
GPIOA =   0x12   # Port value. Write to change, read to obtain value
GPIOB =   0x13
OLLATA =  0x14   # Output latch. Write to latch output.
OLLATB =  0x15


# For the MCP1 :
# On Bank A, there is only the hall sensor output on pin 1
# Set GPA pins as inputs by setting
#  bits of IODIRA register to 1

# Set pins 1 as input
bus.write_byte_data(MCP1,IODIRA,0x01)
 

# Set GPIOA polarity to normal
bus.write_byte_data(MCP1, IOPOLA, 0x00)

# Enable pull up resistor on GPIOA
#bus.write_byte_data(MCP1, GPPUA, 0xFF)

# no mirror interrupts, disable sequential mode, active HIGH
bus.write_byte_data(MCP1, IOCON, 0b00100010)

#Configure interrupt on port A as "interrupt-on-pin change"
bus.write_byte_data(MCP1, INTCONA, 0x00)

#bus.write_byte_data(MCP1, DEFVALA, 0xFF)
#bus.write_byte_data(MCP1, INTCONA, 0xFF)

#Enable interrupt on port A
bus.write_byte_data(MCP1, GPINTENA, 0x01)

#set all outputs to HIGH
#bus.write_byte_data(MCP1, GPIOA, 0xFF)

# Read the INTCAPA to reset the int
bus.read_byte_data(MCP1, INTCAPA)


""" 
for MyData in range(1,16):
  # Count from 1 to 8 which in binary will count
  # from 001 to 111
  bus.write_byte_data(DEVICE,OLLATA,0x1)
  time.sleep(1)
  bus.write_byte_data(DEVICE,OLLATA,0x0)
  time.sleep(1)
"""

#Hall pulse queue
hall_pulse_queue = Queue()

def hall_callback(hall_pin):
  
  print('Edge detected on MCP1 Hall sensor pin %s' %hall_pin)
  MCP1_status = bus.read_byte_data(MCP1, INTCAPA)
  if MCP1_status & 0b0 == 0:
    hall_pulse_queue.put(time.time())
    print("MCP1 pins status: ", bin(MCP1_status))
  #temp
  #time.sleep(0.5)
  bus.read_byte_data(MCP1, INTCAPA)
  #bus.read_byte_data(MCP1, INTCAPB)
 
# add rising edge detection on a channel
GPIO.add_event_detect(mcp1_inta_pin, GPIO.RISING, callback=hall_callback)
#reset interrupt on mcp, or an already active interrupt 
#would disable a new one, rendering the mcp unusable.
#bus.read_byte_data(MCP1, INTCAPA) 




