#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, datetime
import argparse
#from datetime import datetime
from math import sin, cos, sqrt, atan2, asin, radians
from dateutil.tz import tzlocal
from lib_temp.exif_read import ExifRead as EXIF
import json
from shapely.geometry import Point, GeometryCollection, shape

def arg_parse():
    parser = argparse.ArgumentParser(
        description="Search for distance based duplicate images and move them in a 'duplicate' subfolder. Search for image in geofence zones and move them in a 'geofence' subfolder"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="paths to the images folders",
    )
    parser.add_argument(
        "-d",
        "--duplicate_distance",
        type=float,
        default=0.5,
        help="min distance in meter for duplicate image detection"
    )
    parser.add_argument(
        "-j",
        "--json_file",
        help="Path to the geojson file containing geofence polygons",
        default=None,
        #required=True
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

    file_list = [os.path.join(os.path.abspath(directory), file) for file in os.listdir(directory) if file.lower().endswith(".jpg")]

    files = []
    # get DateTimeOriginal data from the images and sort the list by timestamp
    for filepath in file_list:
        metadata = EXIF(filepath)
        #metadata.read()
        try:
            t = metadata.extract_capture_time()
            lon, lat = metadata.extract_lon_lat()
            #print(filepath, lon, lat)
            #print(type(t))
            #s = metadata["Exif.Photo.SubSecTimeOriginal"].value
            files.append((filepath, t, lon, lat))
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filepath, e))
    
    files.sort(key=lambda timestamp: timestamp[1])
    #print_list(files)
    return files

def import_geojson(geojson_file, properties_key):
    """
    import the geojson file and create a dict with the commune's name as the key
    and a shape object as the value
    """
    with open(geojson_file) as f:
        features = json.load(f)["features"]
    GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in features])
    areas = {}
    for feature in features:
        area_name = feature["properties"][properties_key]
        area_shape = shape(feature["geometry"])
        areas[area_name] = area_shape

    return areas


def check_point_in_polygon(point, area_shape):

    return area_shape.contains(point)


def find_polygon(point, area_shapes, first_check=None):
    """
    find outer polygon for each image (store the previous correct polygon to speed up calculation
     time as the next image will probably be in the same one)
    """
    if first_check is not None:
        if check_point_in_polygon(point, area_shapes[first_check]):
            return first_check

    for area in area_shapes:
        if check_point_in_polygon(point, area_shapes[area]):
            return area

#==============================================================================
# Fonction |  ComputeDist
#------------------------------------------------------------------------------
# Calcule la distance entre 2 point (lat/lon)
#
def ComputeDist(PLat, PLon, CLat, CLon):
    try:
        dDST=0
        # Rayon moyen de la terre
        #
        rEquateur = 6378.137	# Rayon équateur (km) : 6378.137
        rPole =     6356.752	# Rayon polaire (km)  : 6356.752

        # Estimation du rayon à la latitude recue
        #
        radius = rPole + (CLat * (rEquateur - rPole) / 90)

        # Distance LAT/LON parcourue depuis le dernier appel
        #
        CLon, CLat = map(radians, [CLon, CLat])
        PLon, PLat = map(radians, [PLon, PLat])

        deltaLat = (CLat - PLat)
        deltaLon = (CLon - PLon)

        a = sin(deltaLat / 2) ** 2 + cos(CLat) * cos(PLat) * sin(deltaLon / 2) ** 2
        c = 2 * asin(sqrt(a))
        dDST = (radius * c) *1000
        #if dDST<1:
        #    print("Distance {} !!".format(dDST))
    except Exception as e:
        print("   !!! ComputeDist EXCEPT [%s] " % e)
    return dDST

def ConvertDMS_DDD(pos):
    dd = float(pos[0]) + float(pos[1])/60 + float(pos[2])/(60*60)
    return dd

            
def move_to_subfolder(file_list, destination_path):
    for file in file_list:
        os.replace(file[0], os.path.join(destination_path, os.path.basename(file[0])))

def main(path):
    
    if args.json_file is not None:
        area_dict = import_geojson(args.json_file, "name")
        print("{} polygons loaded".format(len(area_dict)))
        previous_area = None
        geofence_list = []
    #print(area_dict)
    images_list=list_images(path)
    print("Path is:  ", path)
    prev_lat = 0
    prev_long = 0
    #pp = pprint.PrettyPrinter()
    #pp.pprint(images_list)
    starttime = images_list[0][1]
    duplicate_list = []
    for image in images_list:
        current_lat = image[3]
        current_long = image[2]
        img_distance = ComputeDist(prev_lat, prev_long, current_lat, current_long)
        if img_distance < args.duplicate_distance:
            duplicate_list.append(image)
            continue
        prev_lat = current_lat
        prev_long = current_long
        if args.json_file is not None:
            area = find_polygon(Point(image[2], image[3]), area_dict, previous_area)
            if area is not None:
                previous_area = area
                geofence_list.append(image)

    print("{} duplicates found".format(len(duplicate_list)))
    print("{} images inside geofence zone".format(len(geofence_list)))
    if len(duplicate_list)>0:
        os.makedirs(os.path.join(path, "duplicate"), exist_ok = True)
        move_to_subfolder(duplicate_list, os.path.join(path, "duplicate"))
    if len(geofence_list)>0:
        os.makedirs(os.path.join(path, "geofence"), exist_ok = True)
        move_to_subfolder(geofence_list, os.path.join(path, "geofence"))
                  
if __name__ == '__main__':
    args=arg_parse()
    for _path in args.paths:
        for sub_path in [f.path for f in os.scandir(_path) if f.is_dir()]:
            print(sub_path)
            main(sub_path)

    print("End of Script")
	

