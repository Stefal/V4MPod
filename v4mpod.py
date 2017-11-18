import smbus
import time
import RPi.GPIO as GPIO
import PyCmdMessenger

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

cam_range=0b00011111

# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0
 
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1
Keypressed = False
DEVICE =  0x20 # Device address (A0-A2)
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

# Set all GPA pins as outputs by setting
# all bits of IODIRA register to 0
bus.write_byte_data(DEVICE,IODIRA,0x00)
 
# Set output all 7 output bits to 0
bus.write_byte_data(DEVICE,OLLATA,0)

# Set GPIOA polarity to normal
bus.write_byte_data(DEVICE, IOPOLA, 0)

# Set GPIOB pins as inputs
bus.write_byte_data(DEVICE,IODIRB, 0xFF)
# Enable pull up resistor on GPIOB
bus.write_byte_data(DEVICE, GPPUB, 0xFF)
#Set GPIOB polarity as inverted
bus.write_byte_data(DEVICE,IOPOLB, 0xFF)

# no mirror interrupts, disable sequential mode, active HIGH
bus.write_byte_data(DEVICE, IOCON, 0b01100010)

#Enable interrupt on port B
bus.write_byte_data(DEVICE, GPINTENB, 0xFF)

""" 
for MyData in range(1,16):
  # Count from 1 to 8 which in binary will count
  # from 001 to 111
  bus.write_byte_data(DEVICE,OLLATA,0x1)
  time.sleep(1)
  bus.write_byte_data(DEVICE,OLLATA,0x0)
  time.sleep(1)
"""
# Set Rpi.GPIO to BCM mode
GPIO.setmode(GPIO.BCM)

# Channel used to receive MCP interrupts
channel = 17

# Set this channel as input
GPIO.setup(channel, GPIO.IN)

def my_callback(channel):
    #print('This is a edge event callback function!')
    print('Edge detected on channel %s'%channel)
    #print('This is run in a different thread to your main program')
    global Keypressed
    Keypressed = True

# add rising edge detection on a channel
GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback)  

#Hall sensor pin
hall_pin=25

# Set this channel as input
GPIO.setup(hall_pin, GPIO.IN)
GPIO.setup(hall_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def hall_callback(hall_pin):
  print('Edge detected on pin %s' %hall_pin)
  takePic(cam_range)
  lcd_write_text("Picture", 1)

GPIO.add_event_detect(hall_pin, GPIO.FALLING, callback=hall_callback)

"""
void handleKeypress ()
{
  unsigned int keyValue = 0;
  
  delay (100);  // de-bounce before we re-enable interrupts
  
  keyPressed = false;  // ready for next time through the interrupt service routine
  digitalWrite (ISR_INDICATOR, LOW);  // debugging
  
  // Read port values, as required. Note that this re-arms the interrupts.
  if (expanderRead (INFTFA))
    keyValue |= expanderRead (INTCAPA) << 8;    // read value at time of interrupt
  if (expanderRead (INFTFB))
    keyValue |= expanderRead (INTCAPB);        // port B is in low-order byte
  
  Serial.println ("Button states");
  Serial.println ("0                   1");
  Serial.println ("0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5");
  
  // display which buttons were down at the time of the interrupt
  for (byte button = 0; button < 16; button++)
    {
    // this key down?
    if (keyValue & (1 << button))
      Serial.print ("1 ");
    else
      Serial.print ("0 ");
    
    } // end of for each button

  Serial.println ();
  
  // if a switch is now pressed, turn LED on  (key down event)
  if (keyValue)
    {
    time = millis ();  // remember when
    digitalWrite (ONBOARD_LED, HIGH);  // on-board LED
    }  // end if
  
}  // end of handleKeypress
"""
def handleKeyPress():
  print("In handleKeyPress function")
  KeyValue = 0
  time.sleep(0.1)
  global Keypressed
  Keypressed = False
  if bus.read_byte_data(DEVICE, INFTFB):
    KeyValue |= bus.read_byte_data(DEVICE, INTCAPB)
    print(bin(KeyValue))
    if KeyValue & 0b1:
      print("Power down button")
      power_down(cam_range)
      lcd_write_text("Powering down...", 4)
      
    elif KeyValue & 0b10:
      print("Power up button")
      power_up(cam_range)
      lcd_write_text("Powering up..", 15)
      lcd_write_text("Cams ready", 5)
    elif KeyValue & 0b100:
      print("Shutter button")
      takePic(cam_range)
      lcd_write_text("Picture", 1)
      
      

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)

# Initialize library.
disp.begin(contrast=60)

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a white filled box to clear the image.
draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)

# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.
# Some nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

# Write some text.
draw.text((0,8), ' Welcome to ', font=font)
draw.text((0,16), 'V4MPOD v2.01', font=font)


# Display image.
disp.image(image)
disp.display()  

time.sleep(3)

# Clear display.
disp.clear()
disp.display()

def lcd_write_text(lcdtext, timeout=None):
    disp.clear()
    disp.display()
    image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
    
    # Write some text.
    draw.text((0,8), lcdtext, font=font)
    disp.image(image)
    disp.display()
    if timeout:
        time.sleep(timeout)
        disp.clear()
        disp.display()

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard("/dev/ttyACM0",baud_rate=115200, timeout=4)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [
            ["KCommandList", ""],
            ["KTakepic", "bI"],
            ["KPower_up", "b"],
            ["KPower_down", "b"],
            ["KWake_up", ""]
            ]

# Initialize the messenger
c = PyCmdMessenger.CmdMessenger(arduino,commands)

def takePic(cam=0b00000001, pic_id=1):
    c.send("KTakepic", cam, pic_id)
    pic_return = c.receive(arg_formats="bLI")

def power_up(cam=0b00000001):
    c.send("KPower_up", cam)
    
def power_down(cam=0b00000001):
    c.send("KPower_down", cam)



# Loop until user presses CTRL-C
while True:
  if Keypressed:
     handleKeyPress()
  # Read state of GPIOB register
  """MySwitch = bus.read_byte_data(DEVICE,GPIOB)
  
  if MySwitch & 0b00000001 == 0b00000001:
   print("Switch was pressed!")
   

   time.sleep(1)"""

# Set all bits to zero
bus.write_byte_data(DEVICE,OLLATA,0)
