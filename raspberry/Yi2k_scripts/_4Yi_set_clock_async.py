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
        self.cam_writer = None
        self.cam_reader = None
        self.cam_port = cam_port
        self.cam_token = None
        self._isconnected = False
        
    async def connect(self):
        self.cam_reader, self.cam_writer = await asyncio.open_connection(
                self.cam_address, self.cam_port)
        
        self.cam_writer.write('{"msg_id":257,"token":0}'.encode())
        data = await self.cam_reader.read(512).decode()
        while 1:
            data = await self.cam_reader.read(512).decode()
            if "rval" in data:
                break
            else:
                await asyncio.sleep(0.2)
                
        self.cam_token = re.findall('"param": (.+) }',data)[0]
        self._isconnected = True
        
    async def set_datetime(self, a_datetime = strftime("%Y-%m-%d %H:%M:%S", localtime())):
        if self._isconnected:
            tosend = '{{"msg_id":2,"token":{}, "type":"camera_clock", "param":"' %self.cam_token + a_datetime + '"}'
            self.cam_writer.write(tosend.encode())
            await self.cam_reader.read(512).decode()
        else:
            return "Not connected"
            
    async def get_datetime(self):
        if self._isconnected:
            tosend = '{"msg_id":3,"token":%s}' %self.cam_token
            self.cam_writer.write(tosend.encode())
            while 1:
                conf = await self.cam_reader.read(4096).decode()
                if "param" in conf:
                    break
            conf = conf[37:]
            return conf[3:40]
        else:
            return "Not connected"
        
        
    def disconnect(self):
        self.cam_writer.close()
        self._isconnected = False
        
    def isconnected(self):
        if self._isconnected == True:
            return True
        else:
            return False

