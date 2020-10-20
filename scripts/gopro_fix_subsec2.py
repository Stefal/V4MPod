#!/usr/bin/env python
# -*- coding: utf-8 -*-

# les premiers firmware gopro on une erreur sur le stockage de subsectimeoriginal, il faut multiplier la valeur par 10.
# l'horloge interne est un peu trop lente, il faut corriger le timestamp de 0.007%

import os, sys, datetime
import pprint
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

def big_pic_delta(image_list, delta, file_destination): #check if path is ok
    print("delta est", delta)
    image_with_new_timestamp_list=[]
    for i,image in enumerate(image_list):
        new_fulltime= image[1] + datetime.timedelta(seconds=(i*(delta-1)))
        new_datetimeoriginal= new_fulltime.replace(microsecond=0)
        new_subsectimeoriginal="%.6d"%(new_fulltime.microsecond)
        image_with_new_timestamp_list.append((image[0],new_datetimeoriginal, new_subsectimeoriginal))
        print (image[1], 'new time is', new_datetimeoriginal, 'subsec is', new_subsectimeoriginal)
    #print(image_with_new_timestamp_list)
    #print('type de', image_with_new_timestamp_list[0][2], " est ", type(image_with_new_timestamp_list[0][2]))

    ###write_metadata(image_with_new_timestamp_list) #write the new timestamp

    #moving files
    
    if not os.path.exists(file_destination):
        os.makedirs(file_destination)
    for image in image_list:
        path , filename = os.path.split(image[0])
        out_file=file_destination+'/'+filename
        print("moving ", filename, "to ", file_destination)
        os.rename(image[0],out_file)

def interpolate_timestamp(image_list, delta):
    print("delta est", delta)
    image_with_new_timestamp_list=[]
    gap0=next((i for i, v in enumerate(image_list) if v[2] == 0), None)
    if gap0:
        #ajouter 1 seconde à image[gap0]
        image_list[gap0] = (image_list[gap0][0], (image_list[gap0][1] + datetime.timedelta(seconds=1)))
 
    #debug
    #if delta < 1:
     #   import pdb; pdb.set_trace()
        
    for i,image in enumerate(image_list):
        new_fulltime= image_list[0][1] + datetime.timedelta(seconds=(i*delta))
        new_datetimeoriginal= new_fulltime.replace(microsecond=0)
        new_subsectimeoriginal="%.6d"%(new_fulltime.microsecond)
        image_with_new_timestamp_list.append((image[0],new_datetimeoriginal, new_subsectimeoriginal))
        print (image[1], 'new time is', new_datetimeoriginal, 'subsec is', new_subsectimeoriginal)
    #print(image_with_new_timestamp_list)
    #print('type de', image_with_new_timestamp_list[0][2], " est ", type(image_with_new_timestamp_list[0][2]))

    write_metadata(image_with_new_timestamp_list) #write the new timestamp

def write_metadata(image_list):
    for image in image_list:
        #metadata = pyexiv2.ImageMetadata(image[0])
        metadata = ExifEdit(image[0])
        #metadata.read()
        #metadata["Exif.Photo.DateTimeOriginal"] = image[1]
        metadata.add_date_time_original(image[1])
        #metadata["Exif.Photo.SubSecTimeOriginal"] = image[2]
        #metadata.add_subsectimeoriginal(image[2])
        
        metadata.write()
        #print('Writing new timestamp to ', image[0])

def interpolate_fixed_timestamp(image_list, start_time=None, delta=0.5):
    if start_time == None:
        start_time = image_list[0][1]
    print("Timestamp de départ : ", start_time)
    image_with_new_timestamp_list = []
    for i, image in enumerate(image_list):
        new_fulltime= start_time + datetime.timedelta(seconds=(i*delta))
        new_datetimeoriginal= new_fulltime.replace(microsecond=0)
        new_subsectimeoriginal="%.6d"%(new_fulltime.microsecond)
        image_with_new_timestamp_list.append((image[0],new_datetimeoriginal, new_subsectimeoriginal))
        
    
    #print_list(image_with_new_timestamp_list)
    if write_exif_data == "-write":
        print("Writing exif metadata")
        write_metadata(image_with_new_timestamp_list)
    
def generate_group(a_list):
    group_list = []
    for i,j in enumerate(a_list):
        if j[2]<=1:
            group_list.append(j)
            
        elif (j[2]>1 and i > 0):
            #big_gap_list.append((i,j))
            print("gros gap:", i, j[0], j[2])
            if len(group_list) > 1:
                yield group_list
                group_list = []
                group_list.append(j)
            else:
                group_list = []
                group_list.append(j)
                
    yield group_list
            
def move_to_subfolder(file_list, destination_path):
    for file in file_list:
        os.replace(file[0], os.path.join(destination_path, os.path.basename(file[0])))

def main(path):
    images_list=list_images(path)
    print("le chemin est ", path)
    #pp = pprint.PrettyPrinter()
    #pp.pprint(images_list)
    starttime = images_list[0][1]
    rtc_fix = 0.007
    newlist = []
    for image in images_list:
        #fix wrong subsecond
        img_timestamp = image[1].replace(microsecond=image[1].microsecond*10)
        #fix rtc drift
        img_timestamp = img_timestamp - ((img_timestamp - starttime) * rtc_fix/100)
        print("ori : {} - new = {}".format(image[1], img_timestamp))
        newlist.append((image[0], img_timestamp))

    #for image in images_list:
        #fix wrong gopro subsecond value
        #image = (image[0], image[1].replace(microsecond=image[1].microsecond*10))
        #image = (image[0], "prout")

        #image[1] = image[1].replace(year=1976)
    
    #pp.pprint(newlist)
    write_metadata(newlist)
                  
    print("End of Script")

if __name__ == '__main__':
    if len(sys.argv) > 3:
        print("Usage: python intertime.py path")
        raise IOError("Bad input parameters")
    
    #path="e:\\pic"
    #path="E:\\Mapillary\\2016-09-15"
    path = sys.argv[1]
    if len(sys.argv) > 2:
        write_exif_data = sys.argv[2]
    else:
        write_exif_data = None
    main(path)
	

