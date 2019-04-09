#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function


import os, sys, datetime, time, argparse

from dateutil.tz import tzlocal
from lib.geo import interpolate_lat_lon, decimal_to_dms
from lib.gps_parser import get_lat_lon_time_from_gpx, get_lat_lon_time_from_nmea
from lib.exif import EXIF
from LatLon import LatLon, Latitude, Longitude
from geopy.distance import vincenty
from collections import namedtuple

Master_Picture_infos = namedtuple('Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', 'Latitude', 'Longitude', 'Ele'])
Picture_infos = Master_Picture_infos(path=None, DateTimeOriginal=None, SubSecTimeOriginal=None, Latitude=None, Longitude=None, Ele=None)

def arg_parse():
    """ Parse the command line you use to launch the script
    options possibles :
    source_dir, profile, time_offset, gpx file, log file, send to josm, write exif

    Dans le profil on trouvera :
    Le nom des dossiers des caméra
    le nom des caméras ?
    l'angle des caméras par rapport au sens de déplacement
    l'angle des caméras par rapport à l'horizon ???
    la distance par rapport au centre

    """
    parser = argparse.ArgumentParser(description="Script to correlate the Raspberry Pi log and the pictures from the"
                                                 " V4MPOD, and geolocalize them", version="0.1")
    parser.add_argument("source1",
                        help="Path of the first source of the folders with the pictures. Without this parameter, "
                             "the script will use the current directory as the source")
    parser.add_argument("source2", help="Profile's name of the multicam settings", default="v4mbike")
    parser.add_argument("-m", "--max_distance", help="Max distance between two pictures", type=float)

    args = parser.parse_args()
    print(args)
    return args

def list_images(directory):
    """
    Create a list of image namedtuples sorted by capture timestamp.
    @param directory: directory with JPEG files
    @return: a list of image tuples with time, directory, lat,long...
    """
    file_list = []
    for root, sub_folders, files in os.walk(directory):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]

    files = []
    # get DateTimeOriginal data from the images and sort the list by timestamp
    for filepath in file_list:
        metadata = EXIF(filepath)
        try:
            t = metadata.extract_capture_time()
            s = int(t.microsecond / 1000000)
            geo = metadata.extract_geo()
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            ele = geo.get("altitude")
            files.append(Picture_infos._replace(path=filepath, DateTimeOriginal = t, SubSecTimeOriginal = s,
                                                                Latitude = lat, Longitude = lon, Ele = ele))
            # print t
            # print type(t)
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filepath, e))

    files.sort(key=lambda file: file.DateTimeOriginal)
    # print_list(files)
    return files
    
def compare_latlon(piclist1, piclist2, max_distance = 0):
    distance_list=[]
    for pics in zip(piclist1, piclist2):
        pic1, pic2 = pics
        #try:
        distance = vincenty((pic1.Latitude, pic1.Longitude), (pic2.Latitude, pic2.Longitude)).meters
        
        if distance > max_distance:
            #print("{0} meters between {1} and {2}".format(distance, os.path.basename(pic1.path), os.path.basename(pic2.path)))
            distance_list.append((distance, pic1, pic2))
                
            
    return distance_list
            
if __name__ == '__main__':

    args = arg_parse()
    piclist_source1 = list_images(args.source1)
    piclist_source2 = list_images(args.source2)
    mylist = compare_latlon(piclist_source1, piclist_source2, args.max_distance)
    for d in mylist:
        print("{0} meters between {1} and {2}".format(d[0], os.path.basename(d[1].path), os.path.basename(d[2].path)))




