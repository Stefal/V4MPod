#!/usr/bin/env python
# -*- coding: utf-8 -*-


#Descendre ou monter d'un niveau : longueur des listes des niveaux précédents le niveau de destination..
# + position de la ligne + 1 (ne fonctionne pas pour remonter au niveau 1)

menu = [["MenuA", "MenuB", "MenuC", "MenuD"],
        ["MenuA1", "MenuA2"],
        ["MenuB1", "MenuB2", "MenuB3", "MenuB4", "MenuB5"],
        ["MenuC1"],
        ["MenuD1", "MenuD2", "MenuD3", "MenuD4", "MenuD5", "MenuD6", "MenuD7"],
        [0, 0], 0]
#menu = [["MenuA", "MenuB", "MenuC"], ["MenuA1", "MenuA2"], ["MenuB1", "MenuB2", "MenuB3"], ["MenuC1"], ["FuncA1","FuncA2"], ["FuncB1", "FuncB2", "FuncB3"], ["FuncC1"], [0, 0, 0], 0]

class Position:
    def __init__(self, menu, line, level):
        self.Menu=menu
        self.Line=line
        self.Level=level
    def NextLevel(self):
        self.OldLevel=self.Level
        self.Level=self.Level +1
        self.OldLine=self.Line
        self.Line=0
    def PrevLevel(self):
        if self.Level == 1:
            self.Level=self.Level -1
            self.Line=self.OldLine
    def NextLine(self):
        Pass
        #todo


Pos = Position("menu_top", 1, 0)


pos = menu[-2]
level = menu[-1]


def menu_previous_line():
    global menu
    pos = menu[-2]
    level = menu[-1]
    try:
        if pos[level] > 0:
            # monter d'une ligne et rafraichir l'écran
            menu[-2][menu[-1]] -= 1  # actualise la position
            Pos.line = Pos.line -1
            if level == 0:
                print(menu[0][menu[-2][0]])
            if level == 1:
                print(menu[menu[-2][level - 1] + 1][menu[-2][level]])

    except:
        None

def menu_next_line():
    global menu
    pos = menu[-2]
    level = menu[-1]
    try:
        if level == 0 and (pos[0]+1 < len(menu[0])):
            menu[-2][level] += 1  # actualise la position
            print(menu[0][menu[-2][0]])
            Pos.line = Pos.line +1
        if level==1 and (pos[level]+1 < len(menu[pos[level-1]+1])):
            # descendre d'une ligne et rafraichir l'écran
            menu[-2][level] += 1  # actualise la position
            print(menu[menu[-2][level-1]+1][menu[-2][level]])
            Pos.line = Pos.line + 1
    except:
        None

def menu_previous_level():
    global menu
    pos = menu[-2]
    level = menu[-1]
    try:
        if menu[level-1]:
            #print("Afficher menu level +1 de pos[0] ", menu[pos[0] + 1])
            menu[-1] -= 1
            menu[-2][level] = 0
            print(menu[menu[-1]])
            Pos.level = Pos.level -1
    except:
        None

def menu_next_level():
    global menu
    pos = menu[-2]
    level = menu[-1]
    try:
        if menu[pos[level+1]]:
            #print("Afficher menu level +1 de pos[0] ", menu[pos[0] + 1])
            menu[-1] += 1
            print(menu[pos[0]+1])
            Pos.level = Pos.level +1
    except:
        None

