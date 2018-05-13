#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
from PIL import ImageMath

line_height = 0

def create_full_img(menu_list, lcd):
    #Create an image containing all the menus
    image = Image.new('1', (lcd.width,len(menu_list)*line_height+lcd.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0,0,lcd.width,len(menu_list)*11+lcd.height), outline=255, fill=255)
    
    # Write the menu
    for y,elt in enumerate(menu_list):
        draw.text((1,(y*line_height)), elt.tag, font=font)
        # écriture du status à droite
        if elt.attrib.get("status"):
            word = elt.attrib['status']
            word_lenght = draw.textsize(word)[0]
            draw.text((lcd.width - word_lenght, y*line_height), word, font=font)
        
    return image

def create_blanck_img(lcd):
    #Create a blank image with the lcd size
    image = Image.new('1', (lcd.width, lcd.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0,0,lcd.width,lcd.height), outline=255, fill=255)
    return image
    
def crop_img(img, line, lcd):
    xsize, ysize = img.size
    maxlines = lcd.height//line_height - 1
    if (line_height*(line)+line_height) <= lcd.height:
        line=maxlines
    return img.crop((0,(line_height*(line-maxlines)), lcd.width, (line_height*(line-maxlines)+lcd.height)))
    
def invert(img):
    img=img.convert('L')
    img = ImageOps.invert(img)
    img = img.convert('1')
    return img

def create_mask(y1, y2, background_img):
    xsize, ysize = background_img.size
    mask = Image.new('1', (xsize, ysize))
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0,0,xsize,ysize), outline=0, fill=0)
    draw.rectangle((0,y1,xsize,y2), outline=255, fill=255)
    return mask

def img_xor(img1, img2):
    #print("img1 size = ", img1.size)
    #print("img2 size = ", img2.size)
    return ImageMath.eval("convert((a^b), '1')", a=img1, b=img2)
    
def menu_loop2(full_img, menu):
    for x,elt in enumerate(menu):
        mask=create_mask(line_height*x, line_height*(x+1), full_img)
        out=img_xor(full_img,mask)
        out=crop_img(out,x+1)
        back.paste(out, (0,0, lcd.width, lcd.height))
        disp.image(out)
        disp.display()
        time.sleep(1)
    for x,elt in reversed(list(enumerate(menu))):
        mask=create_mask(line_height*x, line_height*(x+1), full_img)
        out=img_xor(full_img,mask)
        out=crop_img(out,x+1)
        back.paste(out, (0,0, lcd.width, lcd.height))
        disp.image(out)
        disp.display()
        time.sleep(1)


def select_line(full_img, background_img, line, lcd):
    #Highlight a line in the full menu, crop it to the lcd size
    #then display it
    #full_img : the image with all the menus
    #background_img : usually an empty image with the same size as the lcd
    #line : the line you want to highlight
    mask=create_mask(line_height*(line), line_height*(line)+line_height, full_img)
    out=img_xor(full_img,mask)
    out=crop_img(out,line, lcd)
    #print("out size : ", out.size)
    #print("back size : ", background_img.size)
    background_img.paste(out, (0,0, lcd.width, lcd.height))
    lcd.display(out)
    
    return out

#menu0=["Menu 1", "Menu 2", "Menu 3 tiop", "Menu 4 ppprfgi", "Menu 5", "Menu 6 ERgp", "MENU7 ttyipg$^ù*§", "MENU8 ttyipg$^ù*§", "menu 9", "MENU 10 "]
#img2=create_full_img(menu0)
#back=create_blanck_img()
