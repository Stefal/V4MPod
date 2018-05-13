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

# TODO ajouter un type aux elements du menu pour dire si ce sont des lignes d'un menu
# ou s'il s'agit d'un élément différent. De cette façon, les fonctions de gestion
# d'appuie sur les boutons up/down/back pourront gérer les différents cas
# if type d'item == menu
# if type d'item == etc..
root = ET.Element("topmenu")
menuA = ET.SubElement(root, "MenuA", item_type = "menu_line", action="mymenu.next_level")
menuB = ET.SubElement(root, "MenuB", item_type = "menu_line", action="mymenu.next_level")
menuC = ET.SubElement(root, "MenuC", item_type = "menu_line", )
menuD = ET.SubElement(root, "MenuD", item_type = "menu_line", )
menuE = ET.SubElement(root, "MenuE", item_type = "menu_line", )
menuF = ET.SubElement(root, "MenuF", item_type = "menu_line", )
menuG = ET.SubElement(root, "MenuG", item_type = "menu_line", )
menuH = ET.SubElement(root, "MenuH", item_type = "menu_line", )
Shutter = ET.SubElement(menuA, "Shutter session", item_type = "menu_line", action="shutter_ctrl.toggle", state_list=["OFF", "ON"], status="OFF")
set_tm = ET.SubElement(menuA, "TimeLapse Settings", item_type = "menu_line", action="mymenu.next_level")
tm_set1 = ET.SubElement(set_tm, "Setting 1", item_type = "menu_line", )
tm_set2 = ET.SubElement(set_tm, "Setting 2", item_type = "menu_line", )
cam_set = ET.SubElement(menuB, "camera choice", item_type = "menu_line", )

class Shutter_Ctrl(object):
    """Classe d'exemple pour les tests
    Elle simule le contrôle d'une session de prises de vue
    """
    def __init__(self):
        self.status = "OFF"
        
    def start(self):
        print("Starting session")
        self.status = "ON"
        return self.status
        
    def stop(self):
        print("Stopping session")
        self.status = "OFF"
        return self.status
        
    def toggle(self):
        if self.status == "OFF":
            self.start()
        elif self.status == "ON":
            self.stop()
        return self.status


def refresh():
    img_menu = lcd_menu.create_full_img(mymenu.get_menu_lines(), lcd)
    lcd_menu.select_line(img_menu, back, mymenu.selected_line, lcd)

def ok_button_pressed():
    """simule la pression sur le bouton ok
    pour tester ce qui doit se produire
    """
    item = mymenu.get_item()
    
    new_state = eval(item.attrib["action"] + "()")
    # La, je vais avoir un problème si une fonction/méthode retourne quelque
    # chose qui n'a rien à voir avec un status à indiquer sur le LCD
    # essayons avec un 2nd 'if', même si c'est moche
    if new_state:
        if item.attrib.get("status"):
            item.attrib["status"] = new_state
    refresh()

def up_button_pressed():
    if mymenu.get_item().attrib["item_type"] == "menu_line":
        mymenu.prev_line()
        refresh()

def down_button_pressed():
    if mymenu.get_item().attrib["item_type"] == "menu_line":
        mymenu.next_line()
        refresh()

def back_button_pressed():
    if mymenu.get_item().attrib["item_type"] == "menu_line":
        mymenu.prev_level()
        refresh()
    
def demo():
    for elt in mymenu.get_menu_lines():
        mymenu.next_line()
        refresh()
        time.sleep(1)
    for elt in mymenu.get_menu_lines():
        mymenu.prev_line()
        refresh()
        time.sleep(1)

mymenu = Position(root)
shutter_ctrl = Shutter_Ctrl()

with canvas(lcd) as draw:
    line_height = draw.textsize("dummy")[1]

with canvas(lcd) as draw:
    word_lenght = draw.textsize("OFF")[0]
    draw.text((0, 15), text="CAM1")
    draw.text((lcd.width - word_lenght, 15), text="OFF")
    

        
# réutilisation des anciennes fonctions d'affichage du v4mpod.
# création des fonctions refresh et demo
lcd_menu.line_height = line_height
back=lcd_menu.create_blanck_img(lcd)

refresh()
