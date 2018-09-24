#! /usr/bin/env python
# encoding: windows-1250
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

srv1.send('{"msg_id":257,"token":0}')
data1 = srv1.recv(512)
if "rval" in data1:
	token1 = re.findall('"param": (.+) }',data1)[0]	
else:
	data1 = srv1.recv(512)
	if "rval" in data1:
		token1 = re.findall('"param": (.+) }',data1)[0]	

srv2.send('{"msg_id":257,"token":0}')
data2 = srv2.recv(512)
if "rval" in data2:
	token2 = re.findall('"param": (.+) }',data2)[0]	
else:
	data2 = srv2.recv(512)
	if "rval" in data2:
		token2 = re.findall('"param": (.+) }',data2)[0]	

srv3.send('{"msg_id":257,"token":0}')
data3 = srv3.recv(512)
if "rval" in data3:
	token3 = re.findall('"param": (.+) }',data3)[0]	
else:
	data3 = srv3.recv(512)
	if "rval" in data3:
		token3 = re.findall('"param": (.+) }',data3)[0]	

srv4.send('{"msg_id":257,"token":0}')
data4 = srv4.recv(512)
if "rval" in data4:
	token4 = re.findall('"param": (.+) }',data4)[0]	
else:
	data4 = srv4.recv(512)
	if "rval" in data4:
		token4 = re.findall('"param": (.+) }',data4)[0]	


# Ca fonctionne :
#tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"2011-01-03 03:57:16"}' %token
#srv.send(tosend)
#srv.recv(512)
myLocTime=strftime("%Y-%m-%d %H:%M:%S", localtime())

tosend1 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token1 + str(myLocTime) + '"}'
tosend2 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token2 + str(myLocTime) + '"}'
tosend3 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token3 + str(myLocTime) + '"}'
tosend4 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token4 + str(myLocTime) + '"}'

srv1.send(tosend1)
srv2.send(tosend2)
srv3.send(tosend3)
srv4.send(tosend4)

srv1.recv(512)
srv2.recv(512)
srv3.recv(512)
srv4.recv(512)

print "Time sets to %s"  %myLocTime

#GET time from cam 1
tosend1 = '{"msg_id":3,"token":%s}' %token1 
srv1.send(tosend1)

while 1:
	conf1 = srv1.recv(4096)
	if "param" in conf1:
		break

conf1 = conf1[37:]
#print type(conf)
print conf1[3:40]

#GET time from cam 2
tosend2 = '{"msg_id":3,"token":%s}' %token2 
srv2.send(tosend2)

while 1:
	conf2 = srv2.recv(4096)
	if "param" in conf2:
		break

conf2 = conf2[37:]
#print type(conf)
print conf2[3:40]

#GET time from cam 3
tosend3 = '{"msg_id":3,"token":%s}' %token3
srv3.send(tosend3)

while 1:
	conf3 = srv3.recv(4096)
	if "param" in conf3:
		break

conf3 = conf3[37:]
#print type(conf)
print conf3[3:40]

#GET time from cam 4
tosend4 = '{"msg_id":3,"token":%s}' %token4
srv4.send(tosend4)

while 1:
	conf4 = srv4.recv(4096)
	if "param" in conf4:
		break

conf4 = conf4[37:]
#print type(conf)
print conf4[3:40]
