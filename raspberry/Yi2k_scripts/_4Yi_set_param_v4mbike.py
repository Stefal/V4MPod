#! /usr/bin/env python
#
# Res Andy 

import os, re, sys, time, socket
from settings import camaddr, cam1addr, cam2addr, cam3addr, cam4addr
from settings import camport, cam1port, cam2port, cam3port, cam4port
from time import localtime, strftime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

srv1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


srv1.connect((cam1addr, cam1port))
srv2.connect((cam2addr, cam2port))
srv3.connect((cam3addr, cam3port))
srv4.connect((cam4addr, cam4port))


srv1.send('{"msg_id":257,"token":0}'.encode())
data1 = srv1.recv(512).decode()
if "rval" in data1:
    token1 = re.findall('"param": (.+) }',data1)[0] 
else:
    data1 = srv1.recv(512).decode()
    if "rval" in data1:
        token1 = re.findall('"param": (.+) }',data1)[0] 

srv2.send('{"msg_id":257,"token":0}'.encode())
data2 = srv2.recv(512).decode()
if "rval" in data2:
    token2 = re.findall('"param": (.+) }',data2)[0] 
else:
    data2 = srv2.recv(512).decode()
    if "rval" in data2:
        token2 = re.findall('"param": (.+) }',data2)[0] 

srv3.send('{"msg_id":257,"token":0}'.encode())
data3 = srv3.recv(512).decode()
if "rval" in data3:
    token3 = re.findall('"param": (.+) }',data3)[0] 
else:
    data3 = srv3.recv(512).decode()
    if "rval" in data3:
        token3 = re.findall('"param": (.+) }',data3)[0] 

srv4.send('{"msg_id":257,"token":0}'.encode())
data4 = srv4.recv(512).decode()
if "rval" in data4:
    token4 = re.findall('"param": (.+) }',data4)[0] 
else:
    data4 = srv4.recv(512).decode()
    if "rval" in data4:
        token4 = re.findall('"param": (.+) }',data4)[0] 


filet = open("options_v4mbike.txt","r").read()
if "\r\n" in filet:
    filek = filet.split("\r\n")
else:
    filek = filet.split("\n")

for line in filek:
    if len(line) > 5:
        if not line.startswith("#"):
            tosend1 = line %token1
            srv1.send(tosend1.encode())
            srv1.recv(512).decode()
for line in filek:
    if len(line) > 5:
        if not line.startswith("#"):
            tosend3 = line %token3
            srv3.send(tosend3.encode())
            srv3.recv(512).decode()
for line in filek:
    if len(line) > 5:
        if not line.startswith("#"):
            tosend4 = line %token4
            srv4.send(tosend4.encode())
            srv4.recv(512).decode()
for line in filek:
    if len(line) > 5:
        if not line.startswith("#"):
            tosend2 = line %token2
            srv2.send(tosend2.encode())
            srv2.recv(512).decode()

srv1.close()
srv2.close()
srv3.close()
srv4.close()
