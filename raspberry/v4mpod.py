# -*- coding: utf-8 -*-
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
import runpy

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
INTFA =  0x0E   # Interrupt flag (read only) : (0 = no interrupt, 1 = pin caused interrupt)
INTFB =  0x0F
INTCAPA = 0x10   # Interrupt capture (read only) : value of GPIO at time of last interrupt
INTCAPB = 0x11
GPIOA =   0x12   # Port value. Write to change, read to obtain value
GPIOB =   0x13
OLLATA =  0x14   # Output latch. Write to latch output.
OLLATB =  0x15

# Set some GPA pins as outputs by setting
#  bits of IODIRA register to 0
bus.write_byte_data(MCP2,IODIRA,0xFF)
 
# Set output all 7 output bits to 0
bus.write_byte_data(MCP2,OLLATA,0)

# Set GPIOA polarity to normal
bus.write_byte_data(MCP2, IOPOLA, 0)

# Set GPIOB pins as inputs
bus.write_byte_data(MCP2,IODIRB, 0x1F)
# Enable pull up resistor on GPIOB
bus.write_byte_data(MCP2, GPPUB, 0x1F)
#Set GPIOB polarity as inverted
bus.write_byte_data(MCP2,IOPOLB, 0x1F)

# Set outputs all 7 output bits to 0
bus.write_byte_data(MCP2,GPIOB, 0x00)

# no mirror interrupts, disable sequential mode, active HIGH
bus.write_byte_data(MCP2, IOCON, 0b00100010)

#Enable interrupt on port A
bus.write_byte_data(MCP2, GPINTENA, 0xFF)

#Enable interrupt on port B
bus.write_byte_data(MCP2, GPINTENB, 0xFF)


# For the MCP1 :

# Set all GPIOA pins as inputs by setting
#  bits of IODIRA register to 1
bus.write_byte_data(MCP1,IODIRA,0xFF)
 

# Set GPIOA polarity to normal
bus.write_byte_data(MCP1, IOPOLA, 0x00)

# Enable pull up resistor on GPIOA
#bus.write_byte_data(MCP1, GPPUA, 0xFF)

# Set GPIOB 0-1 pins as inputs
bus.write_byte_data(MCP1,IODIRB, 0x03)
# Enable pull up resistor on GPIOB
bus.write_byte_data(MCP1, GPPUB, 0x0F)
#Set GPIOB polarity as inverted
bus.write_byte_data(MCP1,IOPOLB, 0xFF)

# no mirror interrupts, disable sequential mode, active HIGH
bus.write_byte_data(MCP1, IOCON, 0b00100010)

#Configure interrupt on port A as "interrupt-on-pin change"
bus.write_byte_data(MCP1, INTCONA, 0x00)

#bus.write_byte_data(MCP1, DEFVALA, 0xFF)
#bus.write_byte_data(MCP1, INTCONA, 0xFF)

#Enable interrupt on port A
bus.write_byte_data(MCP1, GPINTENA, 0xFF)

#Enable interrupt on port B
bus.write_byte_data(MCP1, GPINTENB, 0x03)


#Enable mcp1 gpiob output 8 for usb charger
#bus.write_byte_data(MCP1, GPIOB, 0x80)


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
GPIO.add_event_detect(mcp2_intb_pin, GPIO.RISING, callback=my_callback) 
#reset interrupt on mcp, or an already active interrupt 
#would disable a new one, rendering the mcp unusable.
bus.read_byte_data(MCP2, INTCAPB)
bus.read_byte_data(MCP2, INTCAPA) 

#Hall sensor pin
hall_pin=25

# Set this channel as input
GPIO.setup(hall_pin, GPIO.IN)
GPIO.setup(hall_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Hall pulse queue
hall_pulse_queue = Queue()

def hall_callback(hall_pin):
  hall_pulse_queue.put(time.time())
  print('Edge detected on MCP1 Hall sensor pin %s' %hall_pin)
  #temp
  #time.sleep(0.5)
  bus.read_byte_data(MCP1, INTCAPA)
  #bus.read_byte_data(MCP1, INTCAPB)
 

#GPIO.add_event_detect(hall_pin, GPIO.FALLING, callback=hall_callback)

# add rising edge detection on a channel
GPIO.add_event_detect(mcp1_inta_pin, GPIO.RISING, callback=hall_callback)
#reset interrupt on mcp, or an already active interrupt 
#would disable a new one, rendering the mcp unusable.
#bus.read_byte_data(MCP1, INTCAPA) 

# add rising edge detection on a channel
GPIO.add_event_detect(mcp1_intb_pin, GPIO.RISING, callback=my_callback) 
#reset interrupt on mcp, or an already active interrupt 
#would disable a new one, rendering the mcp unusable.
bus.read_byte_data(MCP1, INTCAPB) 



class shutter_ctrl(threading.Thread):
    """To send shutter to the cameras"""
    def __init__(self, queue, speed_obj, distance_interval = 0, time_interval = 0, mode = "distance", rate = 0):
        """
        param: queue: A queue.Queue object
        param: time_interval: the time interval between each picture in time-base mode
        param: distance_obj: a speedometer class instance
        param: mode: "distance" or "time" base mode
        param: rate: refresh rate
        """ 
        threading.Thread.__init__(self)
        self.queue = queue
        self.distance_interval = distance_interval
        self.time_interval = time_interval
        self.min_time = 1
        self.speed_obj = speed_obj
        self.mode = mode if mode == "time" else "distance"
        self.rate = rate
        self.prev_distance = 0
        self.prev_time = time.time()
        self.prev_sht_rtn = time.time()
        self.shutter_count = 0
        self.cam_range = 15
        self._pause = True
        self._stop = False
        
    def run(self):
        while not self._stop:
            
            while not self._pause:
                if self.mode == "time":
                    self.time_base()
                elif self.mode == "distance":
                    self.distance_base()
                time.sleep(self.rate)
            time.sleep(self.rate)
        
    def time_base(self):
        
        if self.prev_time + self.time_interval <= time.time():
            self.prev_time = time.time()
            print("shutter: {0} for cams {1:b}".format(self.shutter_count, self.cam_range))
            pic_return = mycams.takePic(logqueue, self.cam_range)
            self.shutter_count +=1
            # retardement du prochain déclenchement si la réponse des
            # caméras est trop lente. Il faut ajouter 1 seconde au temps
            # de réponse.
            answer_delay = pic_return[1][1]/1000
            if answer_delay + 1 > self.time_interval:
                self.prev_time += (answer_delay + 1) - self.time_interval
            
            #TODO tenir compte d'un temps minimum entre la réponse et 
            # le prochain déclenchement.
            # A voir si ça ne doit pas plutôt être géré du côté de la gestion
            # des caméras
            #TODO reprendre le code qui vérifie que le déclenchement a eu lieu       
            
    def distance_base(self):
        try:
            time_interval = self.distance_interval / self.speed_obj.speed
            
        except ZeroDivisionError:
            # when speed is 0, add a very long time
            time_interval = time.time() + 360000
        
        self.time_interval = time_interval
        #control de l'augmentation de la distance.
        if self.speed_obj.total_distance > self.prev_distance:
            self.time_base()
            self.prev_distance = self.speed_obj.total_distance
            
        #TODO regarder pourquoi le premier déclenchement après un arrêt
        # du vélo (speed = 0), arrive un peu trop vite.
            
    def stop(self):
        self._pause = True
        self._stop = True
            
    def pause(self):
        self._pause = True
        
    def resume(self):
        self._pause = False
        

class speedometer(threading.Thread):
    """Speed and distance class, which run in a separate thread
    This class read the pulses from a sensor on a wheel, to compute speed and
    distance.
    Each pulse should be a timestamp and is in a queue.
    """
    def __init__(self, wheel_radius, magnet, queue, rate=0.01):
        """init the class with these parameters
        :param wheel_radius: the wheel radius, in meters
        :param magnet: how many magnets are on the wheel
        :param queue: The queue the class should get pulses timestamps from
        :param rate: Refresh speed rate (default to 10 milliseconds)
        """
        threading.Thread.__init__(self)
        self.pulse_distance = wheel_radius*2*3.1415 / magnet
        self.queue = queue
        self.prev_time = time.time()
        self.total_distance = 0
        self.speed = 0
        self.rate = rate
        self._stop = False
    
    def run(self):
        while not self._stop:
            self.read_queue()
            time.sleep(self.rate)
        
    def read_queue(self):
                    
        for pulse_count in range(self.queue.qsize() + 1):
            try:
                pulse_timestamp = self.queue.get(timeout = 2)
                elapsed_time = pulse_timestamp - self.prev_time
                self.speed = self.pulse_distance / elapsed_time
                self.total_distance += self.pulse_distance
                self.prev_time = pulse_timestamp
                
            except queue.Empty:
                self.speed = 0
            
            finally:
                pass
                #print("Distance : {0} - Vitesse : {1}m/s".format(self.total_distance, self.speed))
        # Revéfifier la pertinence de cette solution dans les différents cas :
        # Il faut tenir compte de la vitesse de la rotation de la roue
        # ainsi que de la fréquence d'appel de cette méthode
        # Il y a plusieurs cas "délicats" :
        # la fréquence d'appel de la méthode est inférieure à celle de l'arrivée des pulses
        # la fréquence d'appel de la méthode est supérieure à celle de l'arrivée des pulses
 
    def stop(self):
        self._stop = True
        
        

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
  time.sleep(0.01)
  global Keypressed, keyDown, keyUp, keySelect, keyBack
  Keypressed = False
  if bus.read_byte_data(MCP2, INFTFB):
    KeyValue |= bus.read_byte_data(MCP2, INTCAPB)
    #clear interrupt
    
    print(bin(KeyValue))
    if KeyValue & 0b1:
        print("Key_Right")
        #power_up(cam_range)
        #lcd_write_text("Powering up...", 10)
        #lcd_write_text("Cams ready", 5)
    elif KeyValue & 0b10:
        print("Key_Up")
        #power_down(cam_range)
        #lcd_write_text("Powering down..", 5)
        keyUp = True
        
    elif KeyValue & 0b100:
        print("Key_Left")
        #takePic(cam_range, logqueue, pic_count)
        #lcd_write_text("Picture", 1)
        keyBack = True
        
    elif KeyValue & 0b1000:
        print("Key_Down")
        keyDown = True
        
    elif KeyValue & 0b10000:
        print("Key_Center")
        keySelect = True
        
    #reset interrupt on mcp    
    bus.read_byte_data(MCP2, INTCAPB)
    bus.read_byte_data(MCP2, INTCAPA)
    

  if bus.read_byte_data(MCP1, INFTFB):
    KeyValue |= bus.read_byte_data(MCP1, INTCAPB)
    #clear interrupt
    
    print(bin(KeyValue))
    if KeyValue & 0b1:
      print("Start switch")
      shutter.resume()
      #power_up(cam_range)
      #lcd_write_text("Powering up...", 10)
      #lcd_write_text("Cams ready", 5)
      
    elif KeyValue == 0b0 or KeyValue == 0b10000000:
      print("Stop switch")
      shutter.pause()
      #power_up(cam_range)
      #lcd_write_text("Powering up...", 10)
      #lcd_write_text("Cams ready", 5)
      
    elif KeyValue & 0b10:
      print("Shutter Switch")
      mycams.takePic(logqueue, cam_range)
      
    #reset interrupt on mcp    
    bus.read_byte_data(MCP1, INTCAPB)
      

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=2000000))

# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)

# Initialize library.
disp.begin(contrast=40)

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
    for rpt in range(repeat +1):
        GPIO.output(buzzer_pin,1)
        time.sleep(duration)
        GPIO.output(buzzer_pin,0)
        time.sleep(pause)

def led_blink():
    bus.write_byte_data(MCP2,GPIOB,0x80)
    time.sleep(0.1)
    bus.write_byte_data(MCP2,GPIOB,0x00)
    


class Yi2K_cam_ctrl(object):
    # This class control the Yi2K with an arduino where all camera are connected.
    #TODO: Stocker l'état éteint ou allumé des caméras pour éviter de basculer en mode
    # vidéo par inadvertance.

    def __init__(self, ardu_serial, ardu_baud, cam_range):
        self.ardu_serial = ardu_serial
        self.ardu_baud = ardu_baud
        self.cam_range = cam_range
        self.pic_count = 0
        self.shutter_error = 0
        self.c = None
        
    def connect(self, serial = None, baud = None):
        if serial == None:
            serial = self.ardu_serial
        if baud == None:
            baud = self.ardu_baud

        try: 
            print("Connecting Arduino")
            arduino = PyCmdMessenger.ArduinoBoard(serial, baud, timeout=4)
            commands = [
                    ["KCommandList", ""],
                    ["KTakepic", "bI"],
                    ["KPower_up", "b"],
                    ["KPower_down", "b"],
                    ["KWake_up", ""]
                    ]
            # Initialize the messenger
            self.c = PyCmdMessenger.CmdMessenger(arduino,commands)
            print ("Arduino connecté")

        except Exception as e:
            print("Impossible de se connecter à l'Arduino")
            print(e)
        
    def takePic(self, log_queue, cam = None):
        if cam == None:
            cam = self.cam_range
            
        #TODO ajouter un retard si le délai entre le déclenchement précédent
        # et le nouveau est trop court.
        timestamp=time.time()
        self.c.send("KTakepic", cam, self.pic_count +1)
        pic_return = self.c.receive(arg_formats="bLI")
        #print(pic_return)
        if (cam ^ pic_return[1][0]) != 0:
            self.shutter_error += 1
            beep(0.4, 0.1, 2)
            status="cam error"
        else:
            led_blink()
            status="ok"
            
        #version avec datetime    
        
        print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), datetime.datetime.fromtimestamp(pic_return[2]).strftime('%H:%M:%S.%f')[:-3])
        #version avec time.gmtime
        #print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), time.gmtime(pic_return[2]))

        log_queue.put(str(timestamp) + "," + str(pic_return) + "," + str(bin(cam)) + "," + status + "\n")
        
        
        self.pic_count += 1
        return pic_return
        
    def power_up(self, cam=None):
        if cam == None:
            cam = self.cam_range

        self.c.send("KPower_up", cam)
        time.sleep(6)
        start_return = self.c.receive(arg_formats="b")
        logfile.write(str(start_return) + "\n")
        print(start_return)

    def power_down(self, cam=None):
        if cam == None:
            cam = self.cam_range
            
        self.c.send("KPower_down", cam)
        down_return=self.c.receive()
        logfile.write(str(down_return) + "\n")
        return self.c.receive()

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles). 



"""
try: 
    arduino = PyCmdMessenger.ArduinoBoard("/dev/ttyACM0",baud_rate=115200, timeout=4)
    commands = [
            ["KCommandList", ""],
            ["KTakepic", "bI"],
            ["KPower_up", "b"],
            ["KPower_down", "b"],
            ["KWake_up", ""]
            ]
    # Initialize the messenger
    c = PyCmdMessenger.CmdMessenger(arduino,commands)

except:
    print("Impossible de se connecter à l'Arduino")
    

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
"""
def takePic(cam, log_queue, pic_id=1):
    #TODO ajouter un retard si le délai entre le déclenchement précédent
    # et le nouveau est trop court.
    timestamp=time.time()
    c.send("KTakepic", cam, pic_id)
    pic_return = c.receive(arg_formats="bLI")
    #print(pic_return)
    if (cam ^ pic_return[1][0]) != 0:
        beep(0.4, 0.1, 2)
        status="cam error"
    else:
        beep(0.1)
        status="ok"
    #version avec datetime    
    print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), datetime.datetime.fromtimestamp(pic_return[2]).strftime('%H:%M:%S.%f')[:-3])
    #version avec time.gmtime
    #print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), time.gmtime(pic_return[2]))

    log_queue.put(str(timestamp) + "," + str(pic_return) + "," + str(bin(cam)) + "," + status + "\n")
    
    
    global pic_count
    pic_count += 1
    return pic_return

def picLoop(cam, pic_nbr, pause, logqueue):
    t = threading.currentThread()
    for i in range(pic_nbr-1):
        if  getattr(t, "do_run", True):
            takePic(cam, logqueue, i)
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


def power_up(cam=0b00000001):
    c.send("KPower_up", cam)
    time.sleep(6)
    start_return = c.receive(arg_formats="b")
    logfile.write(str(start_return) + "\n")
    print(start_return)
    
def power_down(cam=0b00000001):
    c.send("KPower_down", cam)
    down_return=c.receive()
    logfile.write(str(down_return) + "\n")
    return c.receive()


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

def _4Yi_set_clock():
    runpy.run_path("/home/pi/V4MPod/raspberry/Yi2k_scripts/_4Yi_set_clock.py")


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
    bus.read_byte_data(MCP2, INTCAPB)
    bus.read_byte_data(MCP2, INTCAPA)
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
    
def open_file():
    global flushthread
    now=datetime.datetime.now()
    filename = os.path.expanduser("~") + "/Documents/Sessions_V4MPOD/cam_log_" + now.strftime("%Y-%m-%d_%H.%M.%S") + ".log"
    logfile=open(filename, "w")
    flushthread=threading.Thread(target=flush_log, args=(logqueue,), name="flushlog")
    flushthread.start()
    return logfile
    
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


menuA = [[{"Name":"Take Pic", "Func":"mycams.takePic", "Param":"logqueue"},
{"Name":"Power up Cams", "Func":"mycams.power_up", "Param":"cam_range"},
 {"Name":"Power down Cams", "Func":"mycams.power_down", "Param":"cam_range"},
 {"Name":"Start TimeLapse", "Func":"shutter.resume", "Param":""},
 {"Name":"Stop TimeLapse", "Func":"shutter.pause", "Param":""},
 {"Name":"Start cam log", "Func":"logfile=open_file", "Param":""},
 {"Name":"Stop Gnss log", "Func":"stop_gnss_log", "Param":""},
 {"Name":"GNSS Info", "Func":"gnss_localization", "Param":""},
 {"Name":"Set Yi clock", "Func":"_4Yi_set_clock", "Param":""},
 {"Name":"Exit", "Func":"exit_loop", "Param":""},
 {"Name":"Power off PI", "Func":"power_down_pi", "Param":""},

 ],
        [0, 0], 0]

# Main

#splash_boot()
#gnss_fix()
keyDown = False
keyUp = False
keySelect = False
keyBack = False
keepRunning=True
flushthread = None
timelapsethread = None
Timelapse = False

logqueue=Queue(maxsize=0)
back=menu.create_blanck_img()
img_menu_top = menu.create_full_img(menuA[0])
current_img=menu.select_line(img_menu_top, back, 1, disp)
start_gnss_log()
logfile=open_file()

#mybike = speedometer(0.35, 1, hall_pulse_queue)
mybike = None
qq = Queue()
shutter = shutter_ctrl(qq, mybike, time_interval = 1.5, mode = "time")
shutter.start()
mycams = Yi2K_cam_ctrl("/dev/ttyACM0", 115200, 0b00001111)
mycams.connect()


# Loop until user presses CTRL-C

while keepRunning:
    time.sleep(0.05)
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



print("end of script")

#exit_prog()
#sys.exit()
#TODO ajouter un GPIO.cleanup() à la fermeture du script

  
