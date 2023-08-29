#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, datetime
import argparse
#from datetime import datetime
from dateutil.tz import tzlocal
from lib.exif_read import ExifRead as EXIF
from lib.exif_write import ExifEdit

def arg_parse():
    parser = argparse.ArgumentParser(
        description="Fix the Yi timestamp bug in my images from 2018"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="paths to the images folders",
    )
    parser.add_argument(
        "-n",
        "--nowrite",
        help="don't write the new timestamp in the image",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="search images in subdirectory",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="release 0.1"
    )
    args = parser.parse_args()
    print(args)
    return args

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
            #print t
            #print type(t)
            #s = metadata["Exif.Photo.SubSecTimeOriginal"].value
            files.append((filepath, t, filepath[-11:-4]))
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filename, e))
    
    files.sort(key=lambda filenumber: filenumber[2])
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
        print('Writing new timestamp to ', image[0])

def generate_group(a_list):
    group_list = []
    for i,j in enumerate(a_list):
        if j[2]<3:
            group_list.append(j)
            
        elif (j[2]>2 and i > 0):
            #big_gap_list.append((i,j))
            print("gros gap:", i, j[0], j[2])
            if len(group_list) > 1:
                yield group_list
                group_list = []
            else:
                group_list = []
                
    yield group_list
            
    
        
def main(path):
    images_list=list_images(path)
    print("le chemin est ", path)

    #on créé une nouvelle liste avec des tuples comprenant le chemin des images, leurs datetimeoriginal, et la différence de temps avec la précédente
    newlist = []
    for i,pic in enumerate(images_list):
        newlist.append((images_list[i][0], images_list[i][1], int((images_list[i][1]-images_list[i-1][1]).total_seconds())))
    
    #Calcul du délai moyen
    print_list(newlist)
    avg = ((newlist[len(newlist)-1][1]-newlist[0][1]).total_seconds()+1)/(newlist[-1][-1] - newlist[0][-1])
    avg_time = ((newlist[len(newlist)-1][1]-newlist[0][1]).total_seconds()+1)/len(newlist)

    print("Le delai moyen nbr image est :", avg)
    print("Le delai moyen temps est :", avg_time)

    #sys.exit()
    #print_list(newlist)
    newlist = []
    rtc_fix = 0.014
    starttime = images_list[0][1]
    start_file_number = int(images_list[0][2])
    for image in images_list:
        img_timestamp = image[1]
        img_timestamp = starttime + datetime.timedelta(seconds=((int(image[2]) - start_file_number) * avg))
        #img_timestamp = img_timestamp + ((img_timestamp - starttime) * rtc_fix/100)
        newlist.append((image[0], img_timestamp))

    

    print_list(newlist)

    if not args.nowrite:
        print("writing new timestamp")
        write_metadata(newlist)
    print("End of Script")

if __name__ == '__main__':
    args=arg_parse()
    for _path in args.paths:
        if args.recursive:
            for sub_path in [f.path for f in os.scandir(_path) if f.is_dir()]:
                print(sub_path)
                main(sub_path)
        elif not args.recursive:
            print(_path)
            main(_path)
	

