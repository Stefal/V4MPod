#! /usr/bin/env python
# encoding: windows-1250
#
# Res Andy 

import os, re, sys, time, socket, asyncio
from settings import camaddr, cam1addr, cam2addr, cam3addr, cam4addr
from settings import camport, cam1port, cam2port, cam3port, cam4port
from time import localtime, strftime

class Yi2K_telnet (object):
    def __init__ (self, cam_address, cam_port = 7878):
        self.cam_address = cam_address
        self.cam_socket = None
        self.cam_port = cam_port
        self.cam_token = None
        self._isconnected = False
        
    def connect(self):
        self.cam_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cam_socket.connect((self.cam_address, self.cam_port))
        self.cam_socket.send('{"msg_id":257,"token":0}'.encode())
        data = self.cam_socket.recv(512).decode()
        while not "rval" in data:
            time.sleep(0.1)
            data = self.cam_socket.recv(512).decode()
        self.cam_token = re.findall('"param": (.+) }',data)[0]
        self._isconnected = True
        
    def set_datetime(self, a_datetime = strftime("%Y-%m-%d %H:%M:%S", localtime())):
        if self._isconnected:
            tosend = '{{"msg_id":2,"token":{}, "type":"camera_clock", "param":"' %self.cam_token + a_datetime + '"}'
            self.cam_socket.send(tosend.encode())
            self.cam_socket.recv(512)
        else:
            return "Not connected"
            
    def get_datetime(self):
        if self._isconnected:
            tosend = '{"msg_id":3,"token":%s}' %self.cam_token
            self.cam_socket.send(tosend.encode())
            while 1:
                conf = self.cam_socket.recv(4096).decode()
                if "param" in conf:
                    break
            conf = conf[37:]
            return conf[3:40]
        else:
            return "Not connected"
        
        
    def disconnect(self):
        self.cam_socket.close()
        self._isconnected = False
        
    def isconnected(self):
        if self._isconnected = True:
            return True
        else:
            return False

