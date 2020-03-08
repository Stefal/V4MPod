#! /usr/bin/env python
#
# Res Andy 

import os, re, sys, time, datetime, socket

# add the script path in sys path because settings can't be
# imported when this script is run with runpy
script_path = os.path.dirname(os.path.abspath(__file__))
if script_path not in sys.path:
    sys.path.append(script_path)

from settings import camaddr, cam1addr, cam2addr, cam3addr, cam4addr
from settings import camport, cam1port, cam2port, cam3port, cam4port
from time import localtime, strftime
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


# Ca fonctionne :
#tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"2011-01-03 03:57:16"}' %token
#srv.send(tosend)
#srv.recv(512)
myLocTime=strftime("%Y-%m-%d %H:%M:%S", localtime())
start_time = time.time()

while time.time() % 1 < 0.5 and time.time() % 1 > 0.7:
    time.sleep(0.05)
myLocTime = (datetime.datetime.now() + datetime.timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
tosend1 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token1 + str(myLocTime) + '"}'
tosend2 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token2 + str(myLocTime) + '"}'
tosend3 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token3 + str(myLocTime) + '"}'
tosend4 = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token4 + str(myLocTime) + '"}'
while time.time() % 1 < 0.95:
    time.sleep(0.05)
    
#tosend = '{"msg_id":2,"token":%s, "type":"camera_clock", "param":"' %token + str(myLocTime) + '"}'


#srv.send(tosend)
#srv.recv(512)

srv1.send(tosend1.encode())
srv2.send(tosend2.encode())
srv3.send(tosend3.encode())
srv4.send(tosend4.encode())
srv1.recv(512)
srv2.recv(512)
srv3.recv(512)
srv4.recv(512)

srv1.close()
srv2.close()
srv3.close()
srv4.close()


print("Time sets to {}".format(myLocTime))
total_time = time.time() - start_time
print("temps écoulé : {}".format(total_time))


