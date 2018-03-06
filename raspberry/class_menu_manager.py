#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET


class Position(object):
    def __init__(self, menu):
        self.menu = menu
        self.position_list = [[list(menu), 0]]

    def next_level(self):
        if len(list(self.position_list[-1][0])) > 0:
            self.position_list.append([list(self.position_list[-1][0][self.position_list[-1][1]]), 0])

    def prev_level(self):
        if len(self.position_list) > 1:
            self.position_list.pop()

    def next_line(self):
        if len(self.position_list[-1][0]) - 1 > self.position_list[-1][1]:
            self.position_list[-1][1] += 1

    def prev_line(self):
        if self.position_list[-1][1] > 0:
            self.position_list[-1][1] -= 1

    def print_menu(self):
        selected = self.position_list[-1][1]
        for i, item in enumerate(self.position_list[-1][0]):
            print(">{0}".format(item.tag)) if i == selected else " {0}".format(item.tag)


root = ET.Element("topmenu")
menuA = ET.SubElement(root, "menuA")
menuB = ET.SubElement(root, "menuB")
menuC = ET.SubElement(root, "menuC")
tm_start = ET.SubElement(menuA, "Start Timelapse")
tm_stop = ET.SubElement(menuA, "Stop Timelapse")
set_tm = ET.SubElement(menuA, "TimeLapse Settings", func="blala()")
tm_set1 = ET.SubElement(set_tm, "Setting 1")
tm_set2 = ET.SubElement(set_tm, "Setting 2")
cam_set = ET.SubElement(menuB, "camera choice")
#list(root)
#tm_start.get("func")
#root[0][2]
mymenu = Position(root)
mymenu.next_level()
mymenu.next_line()
mymenu.print_menu()

