# -*- coding: utf-8 -*-
import os
import sys
import smbus
import time
import datetime
import RPi.GPIO as GPIO
import Yi2k_ctrl
import subprocess
import gpsd
import threading
import runpy
import argparse

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
import lcd_menu as menu

from queue import Queue
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

cam_range=0b00001111
global cams_up

# Set Rpi.GPIO to BCM mode
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# Channel used to receive MCP interrupts
int_pin = 17
# Set this channel as input
GPIO.setup(int_pin, GPIO.IN)

# Channel used for the buzzer
buzzer_pin = 22
GPIO.setup(buzzer_pin, GPIO.OUT)


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

def my_callback(channel):
    #print('This is a edge event callback function!')
    print('Edge detected on channel %s'%channel)
    #print('This is run in a different thread to your main program')
    global Keypressed
    Keypressed = True
    

# add rising edge detection on a channel
GPIO.add_event_detect(int_pin, GPIO.RISING, callback=my_callback) 
#reset interrupt on mcp, or an already active interrupt 
#would disable a new one, rendering the mcp unusable.
bus.read_byte_data(DEVICE, INTCAPB)
bus.read_byte_data(DEVICE, INTCAPA) 

#Hall sensor pin
hall_pin=25

# Set this channel as input
GPIO.setup(hall_pin, GPIO.IN)
GPIO.setup(hall_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def hall_callback(hall_pin):
  print('Edge detected on pin %s' %hall_pin)
  cams_takePic(MyCams,logqueue, cam_range)
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
  global Keypressed, keyDown, keyUp, keySelect, keyBack
  Keypressed = False
  if bus.read_byte_data(DEVICE, INFTFB):
    KeyValue |= bus.read_byte_data(DEVICE, INTCAPB)
    #clear interrupt
    
    print(bin(KeyValue))
    if KeyValue & 0b1:
        print("Power up button")
        cams_power_up(cam_range)
        lcd_write_text("Powering up...", 10)
        lcd_write_text("Cams ready", 5)
    elif KeyValue & 0b10:
        print("Power down button")
        cams_power_down(cam_range)
        lcd_write_text("Pwr cam down..", 5)     
    elif KeyValue & 0b100:
        print("Shutter button")
        cams_takePic(MyCams,logqueue, pic_count, cam_range)
        #lcd_write_text("Picture", 1)
    elif KeyValue & 0b1000:
        print("Select button")
        keySelect = True
    elif KeyValue & 0b10000:
        print("Down button")
        keyDown = True
    elif KeyValue & 0b100000:
        print("Up button")
        keyUp = True
    elif KeyValue & 0b1000000:
        print("Back button")
        keyBack = True
    #reset interrupt on mcp    
    bus.read_byte_data(DEVICE, INTCAPB)
    bus.read_byte_data(DEVICE, INTCAPA)

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)

# Initialize library.
disp.begin(contrast=50)

# Clear display.
disp.clear()
disp.display()

def splash_boot(pause_time=5):
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    boot = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
    
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(boot)
    
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
    disp.image(boot)
    disp.display()  
    
    time.sleep(pause_time)

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

def beep(duration=0.2, pause=0.2, repeat=0):
    for _rpt in range(repeat +1):
        GPIO.output(buzzer_pin,1)
        time.sleep(duration)
        GPIO.output(buzzer_pin,0)
        time.sleep(pause)

def cams_takePic(cameras_obj, log_queue, cams=None, pic_id=1):
    pic_answer = cameras_obj.takePic(cams)
    #pic_answer is a tuple: timestamp, pic_return, cam, status
    log_queue.put(str(pic_answer[0]) + "," + str(pic_answer[1]) + "," + str(pic_answer[2]) + "," + pic_answer[3] + "\n")
    if pic_answer[3] == "ok":
        beep(0.1)
    else:
        beep(0.4, 0.1, 2)
    
    return pic_answer[1]


def picLoop(cam, pic_nbr, pause, logqueue):
    t = threading.currentThread()
    for i in range(pic_nbr-1):
        if  getattr(t, "do_run", True):
            cams_takePic(MyCams, logqueue, cam_range, i)
            time.sleep(pause)
        else:
            break
        
def start_Timelapse():
    global timelapsethread
    timelapsethread=threading.Thread(target=picLoop, args=(cam_range, 100000, 1.3, logqueue,), name="Picloop")
    timelapsethread.start()
    
def stop_Timelapse():
    global timelapsethread
    timelapsethread.do_run = False

def cams_arduino_connect(camera_obj):
    timestamp, answer = camera_obj.connect()
    logfile.write(str(timestamp) + "," + "Arduino connection: " + "," + str(answer) + "\n")
    return answer

def cams_power_up(cameras_obj, cams=None):
    timestamp, answer, cams = cameras_obj.power_up(cams)
    logfile.write(str(timestamp) + "," + str(answer) + "," + str(cams) + "\n")
    return answer

def cams_power_down(cameras_obj, cams=None):
    timestamp, answer, cams = cameras_obj.power_down(cams)
    logfile.write(str(timestamp) + "," + "Power down" + "," + str(cams) + "\n")
    return answer

def start_gnss_log():
    subprocess.call(["gpspipe -d -R -o ~/Documents/Sessions_V4MPOD/`date +%Y-%m-%d_%H.%M.%S`.nmea"], shell=True)
    
def stop_gnss_log():
    subprocess.call(["killall", "gpspipe"])
    
def show_log():
    lcd_write_text(logfile.readline()[-4:], 5)
    menu.display_img(current_img, disp)

def gnss_fix():
    gpsd.connect()
    mode=0
    while mode < 3:
        try:
            packet=gpsd.get_current()
            mode = packet.mode
        except:
            pass
            
    print("Gnss Fix")
    time.sleep(10)

def gnss_localization():
    gpsd.connect()
    timer= 0
    while timer < 5:
        try:
            packet=gpsd.get_current()
            gnss_info = str(packet.position()[0]) + "\n" + str(packet.position()[1]) + "\n" + packet.time[-13:]
            lcd_write_text(gnss_info, 1)
        except:
            gnss_info = "Error"
        timer +=1
    menu.display_img(current_img, disp)
    print(packet.position())
    print(packet.time)

def cams_set_clocks(cameras_obj):
    timestamp, answer = cameras_obj.set_clocks()
    if answer:
        logfile.write(str(timestamp) + "," + "Yi set clock: OK" + "\n")
        beep(0.1)
    else:
        logfile.write(str(timestamp) + "," + "Yi set clock: Can't set clock, communication error" + "\n")
        beep(0.4, 0.1, 2)

def cams_send_settings(cameras_obj):
    answer = cameras_obj.send_settings()
    if answer[1]:
        logfile.write(str(answer[0]) + "," + "Yi send settings: OK" + "\n")
        beep(0.1)
    else:
        logfile.write(str(answer[0]) + "," + "Yi send settings: Can't send settings, communication error" + "\n")
        beep(0.4, 0.1, 2)
        

def arg_parser():
    """parse the command line"""
    parser = argparse.ArgumentParser(description="Main V4MPOD software")
    parser.add_argument("-i", "--interactive", help="Interactive mode to be able to use the command line", action="store_true")

    args = parser.parse_args()
    if args.interactive:
        print("entering interactive mode")
        global keepRunning
        keepRunning=False

def exit_loop():
    global keepRunning
    keepRunning=False

def power_down_pi():
    exit_prog()
    os.system("sudo shutdown -h now")
        
def exit_prog():
    #TODO : stop the flush thread
    global keepRunning
    #try:
    #reset interrupt on mcp    
    bus.read_byte_data(DEVICE, INTCAPB)
    bus.read_byte_data(DEVICE, INTCAPA)
    bus.close()
    stop_gnss_log()
    logfile.write("Exiting" + "\n")
    logfile.close()
    flushthread.do_run = False
    GPIO.cleanup()
    print("Exiting program A")
    keepRunning=False
    #except:
    #    print("Erreur en quittant")
    print("Exiting program B")
    print("Exiting V4MPOD")
    sys.exit()

    
def open_file():
    global flushthread
    now=datetime.datetime.now()
    filename = os.path.expanduser("~") + "/Documents/Sessions_V4MPOD/cam_log_" + now.strftime("%Y-%m-%d_%H.%M.%S") + ".log"
    logfile=open(filename, "w")
    flushthread=threading.Thread(target=flush_log, args=(logqueue,), name="flushlog")
    flushthread.start()
    return logfile


def new_session():
    #TODO vérifier l'état du compteur de photo après création d'une nouvelle session
    global logfile
    logfile.write("Close logfile" + "\n")
    logfile.close()
    flushthread.do_run = False
    #stop gnss log
    stop_gnss_log()
    #start new logfile
    logfile = open_file()
    #start new gnss log
    start_gnss_log()

def flush_log(logqueue):
    #since Python 3.4 file are inheritable. I think it's why
    #flush() alone doesn't work in this thread.
    
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        time.sleep(10)
        try:
            while not logqueue.empty():
                #logfile.write(logqueue.get())
                logline = logqueue.get()
                print (logline)
                logfile.write(logline)
                logqueue.task_done()
            logfile.flush()
            os.fsync(logfile.fileno())
        except:
            None

def menu_previous_line():
    global menuA
    pos = menuA[-2]
    level = menuA[-1]
    try:
        if pos[level] > 0:
            # monter d'une ligne et rafraichir l'écran
            menuA[-2][menuA[-1]] -= 1  # actualise la position
            if level == 0:
                print(menuA[0][menuA[-2][0]])
            if level == 1:
                print(menuA[menuA[-2][level - 1] + 1][menuA[-2][level]])

    except:
        None

def menu_next_line():
    global menuA
    pos = menuA[-2]
    level = menuA[-1]
    try:
        if level == 0 and (pos[0]+1 < len(menuA[0])):
            menuA[-2][level] += 1  # actualise la position
            print(menuA[0][menuA[-2][0]])
        if level==1 and (pos[level]+1 < len(menuA[pos[level-1]+1])):
            # descendre d'une ligne et rafraichir l'écran
            menuA[-2][level] += 1  # actualise la position
            print(menuA[menuA[-2][level-1]+1][menuA[-2][level]])
    except:
        None


menuA = [[{"Name":"Take Pic", "Func":"cams_takePic", "Param":"MyCams, logqueue, cam_range"},
{"Name":"Power up Cams", "Func":"cams_power_up", "Param":"MyCams, cam_range"},
 {"Name":"Power down Cams", "Func":"cams_power_down", "Param":"MyCams, cam_range"},
 {"Name":"Start TimeLapse", "Func":"start_Timelapse", "Param":""},
 {"Name":"Stop TimeLapse", "Func":"stop_Timelapse", "Param":""},
 {"Name":"Start cam log", "Func":"logfile=open_file", "Param":""},
 {"Name":"Stop Gnss log", "Func":"stop_gnss_log", "Param":""},
 {"Name":"GNSS Info", "Func":"gnss_localization", "Param":""},
 {"Name":"Set Yi settings", "Func":"cams_send_settings", "Param":"MyCams"},
 {"Name":"Set Yi clock", "Func":"cams_set_clocks", "Param":"MyCams"},
 {"Name":"Start new session", "Func":"new_session", "Param":""},
 {"Name":"Exit", "Func":"exit_prog", "Param":""},
 {"Name":"Power off PI", "Func":"power_down_pi", "Param":""},

 ],
        [0, 0], 0]

# Main

splash_boot()
gnss_fix()
keyDown = False
keyUp = False
keySelect = False
keyBack = False
keepRunning=True
flushthread = None
timelapsethread = None
Timelapse = False
cams_up = False
pic_count = 0
logqueue=Queue(maxsize=0)
back=menu.create_blanck_img()
img_menu_top = menu.create_full_img(menuA[0])
current_img=menu.select_line(img_menu_top, back, 1, disp)
start_gnss_log()
logfile=open_file()
MyCams = Yi2k_ctrl.Yi2K_cam_ctrl('/dev/ttyACM0', '115200', cam_range)
cams_arduino_connect(MyCams)

#check if interactive mode is enabled
arg_parser()



# Loop until user presses CTRL-C
while keepRunning:
    if Keypressed:
        handleKeyPress()
    if keyDown:
        keyDown=False
        menu_next_line()
        current_img=menu.select_line(img_menu_top, back, (menuA[-2][0])+1, disp)
    if keyUp:
        keyUp=False
        menu_previous_line()
        current_img=menu.select_line(img_menu_top, back, (menuA[-2][0])+1, disp)
    if keySelect:
        keySelect=False
        exec(menuA[0][menuA[-2][0]]["Func"] + "(" + menuA[0][menuA[-2][0]]["Param"] +")")
        print("exec done")

