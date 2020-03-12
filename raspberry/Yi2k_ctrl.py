# -*- coding: utf-8 -*-
import PyCmdMessenger
import time
import datetime
import runpy

class Yi2K_cam_ctrl(object):
    # This class control the Yi2K with an arduino where all camera are connected.
    #TODO: Stocker l'état éteint ou allumé des caméras pour éviter de basculer en mode
    # vidéo par inadvertance.

    def __init__(self, ardu_serial, ardu_baud, cams_range):
        self.ardu_serial = ardu_serial
        self.ardu_baud = ardu_baud
        self.cams_range = cams_range
        self.cams_on = 0
        self.last_sht_time = 0
        self.min_interval = 1.7
        self.pic_count = 0
        self.shutter_error = 0
        self.c = None
        
    def connect(self, serial = None, baud = None):
        # Initialize an ArduinoBoard instance.  This is where you specify baud rate and
        # serial timeout.  If you are using a non ATmega328 board, you might also need
        # to set the data sizes (bytes for integers, longs, floats, and doubles). 

        timestamp=time.time()
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
            return timestamp, True

        except Exception as e:
            return timestamp, e
            
        
    def takePic(self, cams = None):
        if cams == None:
            cams = self.cams_range
            
        #TODO ajouter un retard si le délai entre le déclenchement précédent
        # et le nouveau est trop court.
        timestamp=time.time()
        if timestamp - self.last_sht_time < self.min_interval:
            time.sleep(abs(timestamp - self.last_sht_time - self.min_interval))
            timestamp=time.time()
        self.last_sht_time = timestamp
        self.c.send("KTakepic", cams, self.pic_count +1)
        pic_return = self.c.receive(arg_formats="bLI")
        #print(pic_return)
        if (cams ^ pic_return[1][0]) != 0:
            self.shutter_error += 1
            #beep(0.4, 0.1, 2)
            status="cam error"
        else:
            #led_blink()
            #beep(0.1)
            status="ok"
            
        #version avec datetime    
        print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), datetime.datetime.fromtimestamp(pic_return[2]).strftime('%H:%M:%S.%f')[:-3])
        #version avec time.gmtime
        #print(pic_return[0], pic_return[1][1:3], bin(pic_return[1][0])[2:].zfill(8), time.gmtime(pic_return[2]))

        #log_queue.put(str(timestamp) + "," + str(pic_return) + "," + str(bin(cam)) + "," + status + "\n")
        
        self.pic_count += 1
        return timestamp, pic_return, bin(cams), status
        
    def power_up(self, cams=None):
        if cams == None:
            cams = self.cams_range
        
        timestamp=time.time()
        self.c.send("KPower_up", cams)
        time.sleep(6)
        start_return = self.c.receive(arg_formats="b")
        #logfile.write(str(start_return) + "\n")
        #TODO vérifier l'allumage des cams, et stocker dans cam_on
        """
        if machin success:
            self.cam_on = cam
        else:
            pass
        """
        print(start_return)
        return timestamp, start_return, bin(cams)

    def power_down(self, cams=None):
        if cams == None:
            cams = self.cams_range
            
        timestamp=time.time()
        self.c.send("KPower_down", cams)
        down_return=self.c.receive()
        #TODO actualiser la liste des caméras en fonctionnement
        """
        self.cam_on = self.cam_on ^ cam
        """
        #logfile.write(str(down_return) + "\n")
        return timestamp, down_return, bin(cams)

    def restart_cam(self, cams=None):
        if cams == None:
            cams = self.cams_range
        #powering down cams
        self.power_down(cams)
        self.power_up(cams)

    def is_on(self, cams=None):
        if cams == None:
            cams = self.cams_range
        if cams & self.cams_on == cams:
            return True
        else:
            return False

    def set_clocks(self):
        timestamp=time.time()
        try:
            runpy.run_path("/home/pi/V4MPod/raspberry/Yi2k_scripts/_4Yi_set_clock.py")
            #logfile.write("Yi set clock: OK" + "\n")
            #beep(0.1)
            return timestamp, True
        except:
            #logfile.write("Yi set clock: Can't set clock, communication error" + "\n")
            #beep(0.4, 0.1, 2)
            return timestamp, False

    def send_settings(self):
        timestamp=time.time()
        try:
            runpy.run_path("/home/pi/V4MPod/raspberry/Yi2k_scripts/_4Yi_set_param.py")
            #logfile.write("Yi send settings: OK" + "\n")
            #beep(0.1)
            return timestamp, True
        except:
            #logfile.write("Yi send settings: Can't send settings, communication error" + "\n")
            #beep(0.4, 0.1, 2)
            return timestamp, False
