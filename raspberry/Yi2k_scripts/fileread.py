#-*-coding:utf8;-*-
#qpy:2
#qpy:console

print "This is console module"

import os, re, sys, time, socket
from settings import camaddr
from settings import camport

print(os.path.realpath(__file__))
print(os.curdir)

#la ligne ci dessous est ok !!!
os.chdir(os.path.dirname(os.path.abspath(__file__)))

filet = open("options.txt","r").read()
if "\r\n" in filet:
	filek = filet.split("\r\n")
else:
	filek = filet.split("\n")
	


