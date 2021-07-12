#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Outil pour chercher les secondes où il y a une seule photo, et les déplacer dans des sous groupes.

import os, sys, datetime
#from datetime import datetime
from dateutil.tz import tzlocal
from lib.exif_read import ExifRead as EXIF
from lib.exif_write import ExifEdit

def print_list(list):
    for i, image in enumerate(list):
        print(i, image)

def list_images(directory):
    ''' 
    Create a list of image tuples sorted by capture timestamp.
    @param directory: directory with JPEG files 
    @return: a list of image tuples with time, directory, lat,long...
    '''
    file_list = []
    for root, sub_folders, files in os.walk(directory):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]

    files = []
    # get DateTimeOriginal data from the images and sort the list by timestamp
    for filepath in file_list:
        metadata = EXIF(filepath)
        #metadata.read()
        try:
            t = metadata.extract_capture_time()
            #print(t)
            #print(type(t))
            #s = metadata["Exif.Photo.SubSecTimeOriginal"].value
            files.append((filepath, t))
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filename, e))
    
    files.sort(key=lambda timestamp: timestamp[1])
    #print_list(files)
    return files

def generate_group(a_list):
    group_list = []
    for i,j in enumerate(a_list):
        if i == 0:
            group_list.append(j)
            continue
            
        if (j[1]-a_list[i-1][1] > datetime.timedelta(milliseconds = 500) and i > 0):
            #big_gap_list.append((i,j))
            print("gros gap:", i, j[0], j[1])
            if len(group_list) > 0:
                yield group_list
                group_list = []
                group_list.append(j)
            else:
                group_list = []
                group_list.append(j)
        else:
            group_list.append(j)
                
    yield group_list
    
def detect_subgroup(img_list):

    subgroup = []
    for img in img_list:
        subgroup.append(img)
        if len(subgroup) == 1:
            pass
        elif len(subgroup) > 1 and subgroup[0][1] == img[1]:
            pass
        elif len(subgroup) == 2 and subgroup[0][1] != img[1]:
            print("Trou possible a : ", img[0])
            subgroup = [subgroup[-1]]
        elif len(subgroup) > 2 and subgroup[0][1] != img[1]:
            subgroup = [subgroup[-1]]
        #print("subgroup : ", subgroup)

        
            
def move_to_subfolder(file_list, destination_path):
    for file in file_list:
        #print("deplacement fichier ", file[0])
        os.replace(file[0], os.path.join(destination_path, os.path.basename(file[0])))

def main(path):
    images_list=list_images(path)
    print(images_list[3])
    print("le chemin est ", path)
    print("nbr d'image : ", len(images_list))
    #print(images_list)

    #detect_subgroup(images_list)
    group_number = 1
    for group in generate_group(images_list):
        print("groupe ", group_number)
        print("nbr d'image du groupe : ", len(group))
        try:
            os.mkdir(os.path.join(path, "{:02d}".format(group_number)))
        except FileExistsError as e:
            print(e)
        
        move_to_subfolder(group, os.path.join(path, "{:02d}".format(group_number)))
        group_number +=1
        
    
              
    print("End of Script")

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: python intertime.py path")
        raise IOError("Bad input parameters")
    
    #path="e:\\pic"
    #path="E:\\Mapillary\\2016-09-15"
    path = sys.argv[1]
    
    main(path)
	

