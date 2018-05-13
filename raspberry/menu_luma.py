#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pour les fonts :
from __future__ import unicode_literals

import os
import sys
import random
import time
import datetime
from class_menu_manager import Position
import xml.etree.ElementTree as ET
from PIL import ImageFont
import lcd_menu2 as lcd_menu


from luma.core.render import canvas
from luma.emulator.device import pygame
from luma.core.virtual import history
from luma.core.virtual import viewport
from luma.core.virtual import snapshot
from luma.core.virtual import hotspot

# 1 BASIC WRITING
lcd = pygame()

root = ET.Element("topmenu")
menuA = ET.SubElement(root, "MenuA")
menuB = ET.SubElement(root, "MenuB")
menuC = ET.SubElement(root, "MenuC")
menuD = ET.SubElement(root, "MenuD")
menuE = ET.SubElement(root, "MenuE")
menuF = ET.SubElement(root, "MenuF")
menuG = ET.SubElement(root, "MenuG")
menuH = ET.SubElement(root, "MenuH")
tm_start = ET.SubElement(menuA, "Start Timelapse")
tm_stop = ET.SubElement(menuA, "Stop Timelapse")
set_tm = ET.SubElement(menuA, "TimeLapse Settings", func="blala()")
tm_set1 = ET.SubElement(set_tm, "Setting 1")
tm_set2 = ET.SubElement(set_tm, "Setting 2")
cam_set = ET.SubElement(menuB, "camera choice")


mymenu = Position(root)

with canvas(lcd) as draw:
    line_height = draw.textsize("Édummy")[1]
    for i, line in enumerate(mymenu.get_menu_lines()):
        draw.text((0, i * line_height), text=line)
    
time.sleep(3)

with canvas(lcd) as draw:
    word_lenght = draw.textsize("OFF")[0]
    draw.text((0, 15), text="CAM1")
    draw.text((lcd.width - word_lenght, 15), text="OFF")
    
time.sleep(3)

mymenu.next_level()

with canvas(lcd) as draw:
    for i, line in enumerate(mymenu.get_menu_lines()):
        draw.text((0, i * line_height), text=line)

def refresh():
    lcd_menu.select_line(img_menu_top, back, mymenu.selected_line, lcd)

def demo():
    for elt in mymenu.get_menu_lines():
        mymenu.next_line()
        refresh()
        time.sleep(1)
    for elt in mymenu.get_menu_lines():
        mymenu.prev_line()
        refresh()
        time.sleep(1)
        
# réutilisation des anciennes fonctions d'affichage du v4mpod.
# création des fonctions refresh et demo
lcd_menu.line_height = line_height
back=lcd_menu.create_blanck_img(lcd)
img_menu_top = lcd_menu.create_full_img(mymenu.get_menu_lines(), lcd)
refresh()


