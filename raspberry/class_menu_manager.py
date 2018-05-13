#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET


class Position(object):
    def __init__(self, menu):
        self.menu = menu
        self.position_list = [[list(menu), 0]]
        self.selected_line = 0

    def next_level(self):
        if len(list(self.position_list[-1][0])) > 0:
            self.position_list.append([list(self.position_list[-1][0][self.position_list[-1][1]]), 0])
            self.selected_line = 0

    def prev_level(self):
        if len(self.position_list) > 1:
            self.position_list.pop()
            self.selected_line = self.position_list[-1][1]

    def next_line(self):
        if len(self.position_list[-1][0]) - 1 > self.position_list[-1][1]:
            self.position_list[-1][1] += 1
            self.selected_line += 1

    def prev_line(self):
        if self.position_list[-1][1] > 0:
            self.position_list[-1][1] -= 1
            self.selected_line -= 1
            
    def get_item(self):
        selected = self.position_list[-1][1]
        # bon, eval, ca marche pas
        # eval(self.position_list[-1][0][selected].attrib["action"])
        # return self.position_list[-1][0][selected].attrib["action"]
        return self.position_list[-1][0][selected]
        # regarder ça : (command pattern)
        # https://softwareengineering.stackexchange.com/questions/182093/why-store-a-function-inside-a-python-dictionary )
        
    def activate_item2(self):
        selected = self.position_list[-1][1]
        
        
    def activate_test(self):
        selected = self.position_list[-1][1]
        item = self.position_list[-1][0]
        print(item[selected].attrib["action"])
        print(self.position_list[-1][0][selected].attrib["action"])
        eval(self.position_list[-1][0][selected].attrib["action"])

    def print_menu(self):
        selected = self.position_list[-1][1]
        for i, item in enumerate(self.position_list[-1][0]):
            
            if i == selected:
                print(">{0}".format(item.tag)) 
            else:
                print(" {0}".format(item.tag))
            
    def get_menu_lines(self):
        #menu_list = [i.tag for i in self.position_list[-1][0]]
        menu_list = [i for i in self.position_list[-1][0]]
        #menu_list.append(self.position_list[-1][1])
        return menu_list
        
if __name__ == "__main__":
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

