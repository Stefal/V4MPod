# -*- coding: utf-8 -*-
import PyCmdMessenger
import time
import datetime
import runpy
from os import system
import re
import socket
import json

#live preview : rtsp://address:554/live

class Yi2K_cam_info(object):

    def __init__(self, name, bit, ip):
        self.name = name
        self.bit = bit
        self.ip = ip
        self.is_on = None
        self.battery_level = None
        self.total_pic = None
        self.session_pic = None
        self.sd_space = None
        self.online = None
        self.connected = False
        self.setting_preset = None
        self.status = {"battery_level" : None, "ext_powered": None, "total_space" : None, "free_space" : None, "percent_space" : None, 'image_size': None, 'meter_mode': None, 'system_mode': None}
        self.port = 7878
        self.srv = None
        self.token = None
        self.MSG_CONFIG_GET = 1
        self.MSG_CONFIG_SET = 2
        self.MSG_CONFIG_GET_ALL = 3
        self.MSG_STORAGE_USAGE = 5
        self.MSG_AUTHENTICATE = 257
        self.MSG_BATTERY = 13
        self.MSG_PREVIEW_START = 259
        self.MSG_PREVIEW_STOP = 260
        self.MSG_CAPTURE = 769

    def _socket_connect(self, timeout=5):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.connect((self.ip, self.port))
        srv.settimeout(10)
        jsondata = json.dumps({"msg_id" : self.MSG_AUTHENTICATE, "token" :  0})
        srv.send(jsondata.encode())
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

    def get_setting(self, setting_type):
        #TODO : use dict.get(key) instead of dict[key]
        if self._socket_connect():
            data = {"msg_id":self.MSG_CONFIG_GET, "type" : setting_type}
            data['token'] = self.token
            jsondata = json.dumps(data)
            self.srv.send(jsondata.encode())
            response = json.loads(self.srv.recv(512).decode())
            self._socket_close()

            if response['rval'] != 0:
                return False

            return response
        return False

    def set_setting(self, setting_type, setting_value):
        #TODO : use dict.get(key) instead of dict[key]

        # photo size :
        # set_setting("photo_size", "16M (4608x3456 4:3) / 8M (3264x2448 4:3)"")
        # meter mode
        # set_setting("meter_mode", "center/average/spot")
        #
        # get setting choice : msg_id : 9, param: setting type
        
        if self._socket_connect():
            data = {"msg_id":self.MSG_CONFIG_SET, "type" : setting_type, "param" : setting_value}
            data['token'] = self.token
            jsondata = json.dumps(data)
            self.srv.send(jsondata.encode())
            response = json.loads(self.srv.recv(512).decode())
            self._socket_close()

            if response['rval'] != 0:
                return False

            return True
        return False

    def get_image_capture_infos(self):

        self.status['image_size'] = self.get_setting('photo_size').get("param")
        self.status['meter_mode'] = self.get_setting('meter_mode').get("param")
        self.status['system_mode'] = self.get_setting('system_mode').get("param")

    def wait_for_pic(self, timeout=10):
        # problème lorsqu'on récupère les données et qu'il y a plusieurs messages :
        # json.loads ne fonctionne plus, il faut d'abord séparer les différents
        # messages, ou trouver une autre solution.
        if self.connected:
            #response = json.loads(self.srv.recv(1024).decode())
            start_timestamp = time.time()
            try:
                while True:
                    response = self.srv.recv(1024).decode()
                    for msg in response.split('{ "'):
                        try:
                            jsondata = json.loads('{ "' + msg)
                            if jsondata.get("type") == "photo_taken":
                                return jsondata.get("param")
                        except ValueError:
                            pass
                    if time.time() - start_timestamp > timeout:
                        raise Exception("timed out")

            except Exception as e:
                print("timed out")
                return False
            
        else:
            return False


    def get_battery(self):
        if self._socket_connect():
            data = {"msg_id":self.MSG_BATTERY}
            data['token'] = self.token
            jsondata = json.dumps(data)
            self.srv.send(jsondata.encode())
            response = json.loads(self.srv.recv(512).decode())
            self._socket_close()
            
            if response['type'] == 'adapter':
                self.status['ext_powered'] = True
                self.status['battery_level'] = int(response['param'])
            else:
                self.status['ext_powered'] = False
                self.status['battery_level'] = int(response['param'])
            
            return response

        else:
            return False
            
    def get_storage_info(self):
        if self._socket_connect():
            # get total space
            data = {"msg_id": self.MSG_STORAGE_USAGE, "type": "total"}
            data['token'] = self.token
            jsondata = json.dumps(data)
            self.srv.send(jsondata.encode())
            total_response = json.loads(self.srv.recv(512).decode())
            # get free space
            data = {"msg_id": self.MSG_STORAGE_USAGE, "type": "free"}
            data['token'] = self.token
            jsondata = json.dumps(data)
            self.srv.send(jsondata.encode())
            free_response = json.loads(self.srv.recv(512).decode())
            self._socket_close()

            self.status['total_space'] = total_response['param']
            self.status['free_space'] = free_response['param']
            self.status['percent_space'] = int(self.status['free_space']*100/self.status['total_space'])
            
            return total_response, free_response
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
            # push the position in the list to the single cam attribute
            # dirty or not ??
            cam_info.idx = self.cams_list.index(cam_info)
        
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
            self.set_clocks(*cams_info)
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

    def take_first_pic(self, *cams_info):
        
        timestamp = time.time()
        if len(cams_info) == 0:
            cams_info = self.cams_list
        
        #connect all cam
        for cam_info in cams_info:
            if cam_info.connected != True:
                cam_info._socket_connect()

        #modifying last shutter time to exclude a set_clocks call
        self.last_sht_time = time.time()

        self.takePic(*cams_info)
        result = []
        for cam_info in cams_info:
            result.append({cam_info.name : cam_info.wait_for_pic()})
            cam_info._socket_close()
       
        return timestamp, result

    def power_up(self, *cams_info):
        
        if len(cams_info) == 0:
            cams_info = self.cams_list


        cams_bits = 0
        for cam_info in cams_info:
            #check if cam is already on
            if not cam_info.is_on:
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
        for cam_info in cams_info:
            cam_info.is_on = True

        print(start_return)
        return timestamp, start_return, bin(cams_bits)

    def power_down(self, *cams_info):
        
        if len(cams_info) == 0:
            cams_info = self.cams_list
        
        cams_bits = 0
        for cam_info in cams_info:
            #check if cam is really on
            if cam_info.is_on:
                cams_bits = cams_bits | cam_info.bit
    
        timestamp=time.time()
        self.c.send("KPower_down", cams_bits)
        down_return=self.c.receive()
        #TODO actualiser la liste des caméras en fonctionnement
        """
        self.cam_on = self.cam_on ^ cam
        """
        for cam_info in cams_info:
            cam_info.is_on = False
            cam_info.online = False
        #logfile.write(str(down_return) + "\n")
        return timestamp, down_return, bin(cams_bits)

    def restart_cam(self, *cams_info):
        
        self.power_down(*cams_info)
        self.power_up(*cams_info)

    def is_online(self, *cams_info):
        if len(cams_info) == 0:
            cams_info = self.cams_list
            result = True
            for cam_info in cams_info:
                result = result & cam_info.online
            return result
        if len(cams_info) == 1:
            # in case of single cam request, I want to know if the status is none
            return cams_info[0].online
    
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
                cam_info.is_on = True
            else:
                #TODO ce n'est clairement pas bien, car si je ping une caméra non allumée,
                # elle devient impossible à allumer pusique disparue du cam_range.
                #self.cams_range = self.cams_range & (0b11111111 ^ cam_info.bit)
                cam_info.online = False

        result = True
        for cam_info in cams_info:
            result = result & cam_info.online
        
        #returning a single value for all cams
        #TODO returning separate values for each cam?
        return result

    def check_cams_status(self, *cams_info):
        
        if len(cams_info) == 0:
            cams_info = self.cams_list
        
        for cam_info in cams_info:
            if cam_info.is_on == None or (cam_info.is_on == True and cam_info.online != True):
                #we don't know if cam is on
                #let's ping it
                #if cam is on, we need to ping it too
                self.ping_cams(cam_info, timeout=2)

            if cam_info.online == True:
                cam_info.get_battery()
                cam_info.get_storage_info()
                cam_info.get_image_capture_infos()
        
        #merge status of all cams into a single value
        is_on_list = [cam.is_on for cam in self.cams_list]
        if is_on_list.count(is_on_list[0]) == len(is_on_list):
            self.cams_is_on = is_on_list[0]
        else:
            self.cams_is_on = None

        online_list = [cam.online for cam in self.cams_list]
        if online_list.count(online_list[0]) == len(online_list):
            self.cams_online = online_list[0]
        else:
            self.cams_online = None

        image_size_list = [cam.status['image_size'] for cam in self.cams_list]
        if image_size_list.count(image_size_list[0]) == len(image_size_list):
            self.cams_image_size = image_size_list[0]
        else:
            self.cams_image_size = None

        system_mode_list = [cam.status['system_mode'] for cam in self.cams_list]
        if system_mode_list.count(system_mode_list[0]) == len(system_mode_list):
            self.cams_system_mode = system_mode_list[0]
        else:
            self.cams_system_mode = None

        meter_mode_list = [cam.status['meter_mode'] for cam in self.cams_list]
        if meter_mode_list.count(meter_mode_list[0]) == len(meter_mode_list):
            self.cams_meter_mode = meter_mode_list[0]
        else:
            self.cams_meter_mode = None







