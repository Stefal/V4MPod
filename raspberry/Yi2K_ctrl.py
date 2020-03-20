# -*- coding: utf-8 -*-
import PyCmdMessenger
import time
import datetime
import runpy
from os import system
import re
import socket
import json

class Yi2K_cam_info(object):

    def __init__(self, name, bit, ip):
        self.name = name
        self.bit = bit
        self.ip = ip
        self.battery_level = None
        self.total_pic = None
        self.session_pic = None
        self.sd_space = None
        self.online = False
        self.connected = False
        self.setting_preset = None
        self.port = 7878
        self.srv = None
        self.token = None

    def _socket_connect(self, timeout=5):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.connect((self.ip, self.port))
        srv.send('{"msg_id":257,"token":0}'.encode())
        start_timestamp = time.time()
        token = None
        while token == None:
            data = json.loads(srv.recv(512).decode())
            if "param" in data:
                token = data["param"]
            if time.time() - start_timestamp > timeout:
                break
        
        if token != None:
            self.token = token
            self.srv = srv
            self.connected = True
            return True
        else:
            return False

    def _socket_close(self):
        self.srv.close()
        self.srv = None
        self.token = None
        self.connected = False

    def set_clock(self):
        #TODO use try/except
        if self._socket_connect():
            start_time = time.time()

            while time.time() % 1 < 0.5 and time.time() % 1 > 0.7:
                time.sleep(0.05)
            myLocTime = (datetime.datetime.now() + datetime.timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
            tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %self.token + str(myLocTime) + '"}'
            
            while time.time() % 1 < 0.95:
                time.sleep(0.05)

            self.srv.send(tosend.encode())
            self.srv.recv(512)
            self._socket_close()
            print("Time sets to {}".format(myLocTime))
            total_time = time.time() - start_time
            print("temps écoulé : {}".format(total_time))
            return True
        else:
            return False

    def send_settings(self, *settings):
        if self._socket_connect():
            start_time = time.time()
            for setting in settings:
                setting['token'] = self.token
                self.srv.send(json.dumps(setting).encode())
                self.srv.recv(512)

            self._socket_close()
            return True
        else:
            return False

    def send_file_settings(self, file_path):
        settings = []
        with open(file_path) as file:
            for line in file:
                if not line.startswith("#") and line.startswith('{"msg_id"'):
                    try:
                        settings.append(json.loads(line))
                    except Exception as e:
                        print("Json error: ", e)
                        return False
        
        result = self.send_settings(*settings)
        return True if result else False




            

class Yi2K_cams_ctrl(object):
    # This class control the Yi2K with an arduino where all camera are connected.
    #TODO: Stocker l'état éteint ou allumé des caméras pour éviter de basculer en mode
    # vidéo par inadvertance.

    def __init__(self, ardu_serial, ardu_baud, *cams_info):
        self.ardu_serial = ardu_serial
        self.ardu_baud = ardu_baud
        self.cams_range = 0
        self.cams_list = []
        self.cams_on = 0
        self.last_sht_time = 0
        self.min_interval = 1.7
        self.standby_time = 60
        self.pic_count = 0
        self.shutter_error = 0
        self.c = None
        
        self.add_cams(*cams_info)

    def add_cams(self, *cams_info):
        for cam_info in cams_info:
            self.cams_list.append(cam_info)
            self.cams_range = self.cams_range | cam_info.bit
        
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
            
        
    def takePic(self, *cams_info):

        if len(cams_info) == 0:
            cams_bits = self.cams_range
        else:
            cams_bits = 0
            for cam_info in cams_info:
                cams_bits = cams_bits | cam_info.bit 

        timestamp=time.time()
        #if the new takePic is too "far in time" from the precedent one, the camera are probably in standby mode
        #We need to wake up them, and one solution is to force sync their clocks
        #BON en fait, non, ça ne fonctionne pas, mais je laisse la resynchro quand même pour le moment.
        if timestamp - self.last_sht_time > self.standby_time:
            self.set_clocks()
            print("set clocks")
            timestamp=time.time()

        #If the new takePic is too close to the precedent one, the camera won't respond
        #So we need to wait some
        if timestamp - self.last_sht_time < self.min_interval:
            time.sleep(abs(timestamp - self.last_sht_time - self.min_interval))
            timestamp=time.time()
        self.last_sht_time = timestamp
        self.c.send("KTakepic", cams_bits, self.pic_count +1)
        pic_return = self.c.receive(arg_formats="bLI")
        #print(pic_return)
        if (cams_bits ^ pic_return[1][0]) != 0:
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
        return timestamp, pic_return, bin(cams_bits), status
        
    def power_up(self, *cams_info):
        
        if len(cams_info) == 0:
            cams_bits = self.cams_range
        else:
            cams_bits = 0
            for cam_info in cams_info:
                cams_bits = cams_bits | cam_info.bit 

        timestamp=time.time()
        self.c.send("KPower_up", cams_bits)
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
        return timestamp, start_return, bin(cams_bits)

    def power_down(self, *cams_info):
        
        if len(cams_info) == 0:
            cams_bits = self.cams_range
        else:
            cams_bits = 0
            for cam_info in cams_info:
                cams_bits = cams_bits | cam_info.bit
        timestamp=time.time()
        self.c.send("KPower_down", cams_bits)
        down_return=self.c.receive()
        #TODO actualiser la liste des caméras en fonctionnement
        """
        self.cam_on = self.cam_on ^ cam
        """
        #logfile.write(str(down_return) + "\n")
        return timestamp, down_return, bin(cams_bits)

    def restart_cam(self, *cams_info):
        
        self.power_down(*cams_info)
        self.power_up(*cams_info)

    def is_on(self, cams=None):
        if cams == None:
            cams = self.cams_range
        if cams & self.cams_on == cams:
            return True
        else:
            return False
    
    def set_clocks(self, *cams_info):
        if len(cams_info) == 0:
            cams_info = self.cams_list
        timestamp=time.time()
        try:
            for cam_info in cams_info:
                if not cam_info.set_clock():
                    raise IOError("Can't set clock on {}".format(cam_info.ip))
        except IOError as e:
            return timestamp, False

        return timestamp, True

    def send_settings(self, settings, *cams_info):
        if len(cams_info) == 0:
            cams_info = self.cams_list
        timestamp=time.time()
        try:
            for cam_info in cams_info:
                if not cam_info.send_settings(*settings):
                    raise IOError("Can't send setting to {}".format(cam_info.ip))
        except IOError as e:
            return timestamp, False

        return timestamp, True

    def send_file_settings(self, file_path, *cams_info):
        if len(cams_info) == 0:
            cams_info = self.cams_list
        timestamp=time.time()
        try:
            for cam_info in cams_info:
                cam_info.send_file_settings(file_path)
        except Exception as e:
            print("Error send file settings: {}".format(e))
            return timestamp, False
        return timestamp, True

    def ping_cams(self, *cams_info, timeout=10):
        if len(cams_info) == 0:
            cams_info = self.cams_list
        
        for cam_info in cams_info:
            start_timestamp = time.time()
            response = None
            while response != 0:
                response = system("ping -c 1 " + cam_info.ip + " > /dev/null")
                if time.time() - start_timestamp > timeout:
                    break
            if response == 0:
                        
                #TODO Verifier s'il est bien pertinent de mettre à jour
                #cam_range aussitôt. Il pourrait être préférable de demander
                #une action de l'utilisateur pour désactiver une caméra qui ne
                #serait pas joignable.
                self.cams_range = self.cams_range | cam_info.bit
                cam_info.online = True
            else:
                self.cams_range = self.cams_range & (0b11111111 ^ cam_info.bit)
                cam_info.online = False

        result = True
        for cam_info in cams_info:
            result = result & cam_info.online
        return result
