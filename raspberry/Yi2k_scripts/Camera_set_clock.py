#! /usr/bin/env python
#
# Res Andy 

import os, re, sys, time, socket
from settings import camaddr
from settings import camport
from time import localtime, strftime
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.connect((camaddr, camport))

srv.send('{"msg_id":257,"token":0}')

data = srv.recv(512)
if "rval" in data:
	token = re.findall('"param": (.+) }',data)[0]	
else:
	data = srv.recv(512)
	if "rval" in data:
		token = re.findall('"param": (.+) }',data)[0]	

print data
# Ca fonctionne :
#tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"2011-01-03 03:57:16"}' %token
#srv.send(tosend)
#srv.recv(512)
myLocTime=strftime("%Y-%m-%d %H:%M:%S", localtime())
tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token + str(myLocTime) + '"}'
srv.send(tosend)
srv.recv(512)
