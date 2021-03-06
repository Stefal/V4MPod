#! /usr/bin/env python
#
# Res Andy 

import os, re, sys, time, socket
from settings import camaddr, cam1addr, cam2addr, cam3addr, cam4addr
from settings import camport, cam1port, cam2port, cam3port, cam4port
from time import localtime, strftime, sleep
#srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#srv.connect((camaddr, camport))
srv1.connect((cam1addr, cam1port))
srv2.connect((cam2addr, cam2port))
srv3.connect((cam3addr, cam3port))
srv4.connect((cam4addr, cam4port))

#srv.send('{"msg_id":257,"token":0}')
srv1.send('{"msg_id":257,"token":0}'.encode())
srv2.send('{"msg_id":257,"token":0}'.encode())
srv3.send('{"msg_id":257,"token":0}'.encode())
srv4.send('{"msg_id":257,"token":0}'.encode())

"""
data = srv.recv(512)
if "rval" in data:
    token = re.findall('"param": (.+) }',data)[0]   
else:
    data = srv.recv(512)
    if "rval" in data:
        token = re.findall('"param": (.+) }',data)[0]   
"""

data1 = srv1.recv(512).decode()
if "rval" in data1:
    token1 = re.findall('"param": (.+) }',data1)[0] 
else:
    data1 = srv1.recv(512).decode()
    if "rval" in data1:
        token1 = re.findall('"param": (.+) }',data1)[0] 


data2 = srv2.recv(512).decode()
if "rval" in data2:
    token2 = re.findall('"param": (.+) }',data2)[0] 
else:
    data2 = srv2.recv(512).decode()
    if "rval" in data2:
        token2 = re.findall('"param": (.+) }',data2)[0] 

data3 = srv3.recv(512).decode()
if "rval" in data3:
    token3 = re.findall('"param": (.+) }',data3)[0] 
else:
    data3 = srv3.recv(512).decode()
    if "rval" in data3:
        token3 = re.findall('"param": (.+) }',data3)[0] 

data4 = srv4.recv(512).decode()
if "rval" in data4:
    token4 = re.findall('"param": (.+) }',data4)[0] 
else:
    data4 = srv4.recv(512).decode()
    if "rval" in data4:
        token4 = re.findall('"param": (.+) }',data4)[0] 


tosend1 = '{"msg_id":769,"token":%s}' %token1
tosend2 = '{"msg_id":769,"token":%s}' %token2
tosend3 = '{"msg_id":769,"token":%s}' %token3
tosend4 = '{"msg_id":769,"token":%s}' %token4

count=10000

while count > 1:
    srv1.send(tosend1.encode())
    srv2.send(tosend2.encode())
    srv3.send(tosend3.encode())
    srv4.send(tosend4.encode())
    print("Photo ", count)
    time.sleep(4)
    count = count - 1

srv1.recv(512)
srv2.recv(512)
srv3.recv(512)
srv4.recv(512)


#   time.sleep(2)
#   count = count - 1

srv1.close()
srv2.close()
srv3.close()
srv4.close()
