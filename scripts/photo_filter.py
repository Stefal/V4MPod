#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, datetime
import argparse
from math import sin, cos, sqrt, atan2, asin, radians
import time
from lib_temp.exif_read import ExifRead as EXIF
import json
from shapely.geometry import Point, GeometryCollection, shape
from collections import namedtuple
import xml.etree.ElementTree as ET
import urllib.request, urllib.parse, urllib.error

#TODO: calculate G force (using image position, and speed), to alert on impossible movement.
Picture_infos = namedtuple('Picture_infos',
                               ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', "Longitude", "Latitude", "Ele", "ImgDirection"])

def arg_parse():
    parser = argparse.ArgumentParser(
        description="Search for distance based duplicate images and move them in a 'duplicate' subfolder. Search for image in geofence zones and move them in a 'geofence' subfolder"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to the images folders",
    )
    parser.add_argument(
        "-d",
        "--duplicate_distance",
        type=float,
        default=0.5,
        help="Min distance in meter for duplicate image detection"
    )
    parser.add_argument(
        "-j",
        "--json_file",
        help="Path to the geojson file containing geofence polygons",
        default=None,
        #required=True
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="Search images in subdirectory",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-t",
        "--max_turn_angle",
        help="check if two subsequent images have a too large direction angle. The result will be send to Josm as a session, with some previous and following images.",
        default=25,
        type=float,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="release 0.2"
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
            img_direction = metadata.extract_direction()
            #print(filepath, lon, lat)
            #print(type(t))
            #s = metadata["Exif.Photo.SubSecTimeOriginal"].value
            files.append(Picture_infos(path=filepath, DateTimeOriginal = t,
                                                                SubSecTimeOriginal = None,
                                                                Latitude = lat,
                                                                Longitude = lon,
                                                                Ele = None,
                                                                ImgDirection = img_direction))
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filepath, e))
    
    files.sort(key=lambda file: file.DateTimeOriginal)
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
        
def write_josm_session(piclists, session_file_path, cam_names, gpx_file=None, new_coord=False):
    """
    Build a josm session file in xml format with all the pictures on separate layer, and another
    layer for the gpx/nmea file
    :param piclists: a list of list of New_Picture_infos namedtuple
    :param session_file_path: the path and name of the session file
    :param cam_names: The camera's name, which will be the layer's name
    :param gpx_file: The path of the gpx/nmea file.
    :param new_coord: write in the image layer if the coordinates are new or not.
    """

    root = ET.Element("josm-session")
    root.attrib = {"version": "0.1"}
    viewport = ET.SubElement(root, "viewport")
    projection = ET.SubElement(root, "projection")
    layers = ET.SubElement(root, "layers")

    # view_center = ET.SubElement(viewport, "center")
    # view_center.attrib = {"lat":"47.7", "lon":"-2.16"}
    # view_scale = ET.SubElement(viewport, "scale")
    # view_scale.attrib = {'meter-per-pixel' : '0.8'}

    proj_choice = ET.SubElement(projection, "projection-choice")
    proj_id = ET.SubElement(proj_choice, "id")
    proj_id.text = "core:mercator"
    proj_core = ET.SubElement(projection, "code")
    proj_core.text = "EPSG:3857"

    for i, piclist in enumerate(piclists):
        layer = ET.SubElement(layers, "layer")
        layer.attrib = {"index": str(i), "name": str(cam_names[i]), "type": "geoimage", "version": str(0.1),
                        "visible": "true"}

        show_thumb = ET.SubElement(layer, "show-thumbnails")
        show_thumb.text = "false"

        for pic in piclist:
            try:
                geoimage = ET.SubElement(layer, "geoimage")
                g_file = ET.SubElement(geoimage, "file")
                g_file.text = pic.path
                g_thumb = ET.SubElement(geoimage, "thumbnail")
                g_thumb.text = "false"
                g_position = ET.SubElement(geoimage, "position")
                g_position.attrib = {"lat": str(pic.Latitude), "lon": str(pic.Longitude)}
                g_elevation = ET.SubElement(geoimage, "elevation")
                #g_elevation.text = str(pic.Ele)
                # g_gps_time = ET.SubElement(geoimage, "gps-time")
                # josm concatenate the timestamp second and microsecond
                # g_gps_time.text = str(int(time.mktime(pic.New_DateTimeOriginal.timetuple()))) + str(int(round(pic.New_DateTimeOriginal.microsecond/1000,  0)))
                g_exif_orientation = ET.SubElement(geoimage, "exif-orientation")
                g_exif_orientation.text = "1"
                g_exif_time = ET.SubElement(geoimage, "exif-time")
                # josm concatenate the timestamp second and microsecond (1531241239.643 becomes 1531241239643)
                # TODO ne fonctionne pas tout le temps, pour peillac, ne marche pas avec E:\Mapillary\2017-10-07_16H24mn00s\avant\2017-10-07_16H26mn43s-Cam_avant-YDXJ0130.jpg (microsecond = 7538)
                # Normalement, c'est corrigé
                # TODO faire des tests.
                g_exif_time.text = str(int(time.mktime(pic.DateTimeOriginal.timetuple()))) + "%.3d" % round(
                    pic.DateTimeOriginal.microsecond / float(1000), 0)
                g_exif_direction = ET.SubElement(geoimage, "exif-image-direction")
                g_exif_direction.text = str(pic.ImgDirection)
                if new_coord:
                    g_is_new_gps = ET.SubElement(geoimage, "is-new-gps-data")
                    g_is_new_gps.text = "true"
            except Exception as e:
                print("Skipping {} - {}".format(pic.path, e))

    if gpx_file is not None:
        gpx_layer = ET.SubElement(layers, "layer")
        gpx_layer.attrib = {"index": str(len(piclists) + 1), "name": gpx_file.split("\\")[-1], "type": "tracks",
                            "version": "0.1", "visible": "true"}
        gpx_file_layer = ET.SubElement(gpx_layer, "file")
        gpx_file_layer.text = urllib.parse.urljoin('file:', urllib.request.pathname2url(gpx_file))

    myxml = ET.ElementTree(root)

    try:
        os.path.isdir(os.path.split(session_file_path)[0])
        myxml.write(session_file_path)
    except:
        print("The folder to write the session file doesn't exists")
        return myxml


def open_session_in_josm(session_file_path, remote_port=8111):
    """Send the session file to Josm. "Remote control" and "open local files" must be enable in the Josm settings
     :param session_file_path: the session file path (.jos)
     :param remote_port: the port to talk to josm. Default is 8111"""
    import urllib.request, urllib.error, urllib.parse
    #TODO utiliser 127.0.0.1:8111/version pour vérifier si josm est en route et le remote actif.
    #TODO gérer les cas ou le chemin de fichier comporte des caractères accentués. L'idéal serait un passage
    # a python 3, mais je doute que les dépendances le gère correctement.
    session_file_path = urllib.parse.quote(session_file_path)

    print("Opening the session in Josm....", end="")
    print("http://127.0.0.1:" + str(remote_port) + "/open_file?filename=" + session_file_path)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:" + str(remote_port) + "/open_file?filename=" + session_file_path)
        answer = r.read()
        print("Success!") if "OK" in answer.decode() else print("Error!")
        r.close()
    except Exception as e:
        print("Error! Can't send the session to Josm: ", e)
def main(path):
    trailing_pics = 10
    if args.json_file is not None:
        area_dict = import_geojson(args.json_file, "name")
        print("{} polygons loaded : {}".format(len(area_dict), list(area_dict.keys())))
        previous_area = None
        geofence_list = []
    #print(area_dict)
    images_list=list_images(path.path)
    #print("type path is: ", type(path))
    prev_lat = 0
    prev_long = 0
    prev_direction = images_list[0].ImgDirection
    #pp = pprint.PrettyPrinter()
    #pp.pprint(images_list)
    starttime = images_list[0].DateTimeOriginal
    duplicate_list = []
    reverse_list = []
    for i, image in enumerate(images_list):
        current_lat = image.Latitude
        current_long = image.Longitude
        current_direction = image.ImgDirection
        img_distance = ComputeDist(prev_lat, prev_long, current_lat, current_long)
        if img_distance < args.duplicate_distance:
            duplicate_list.append(image)
            continue
        prev_lat = current_lat
        prev_long = current_long
        if args.json_file is not None:
            area = find_polygon(Point(image.Longitude, image.Latitude), area_dict, previous_area)
            if area is not None:
                previous_area = area
                geofence_list.append(image)
                continue
        if abs((current_direction - prev_direction + 180) % 360 - 180) > args.max_turn_angle:
            try:
                for idx in range(trailing_pics):
                    if i-2+idx >= 0 and images_list[i-2+idx] not in reverse_list:
                        reverse_list.append(images_list[i-2+idx])
            except IndexError:
                print("Info: no more image available")
        prev_direction = current_direction

    print("{} duplicates found".format(len(duplicate_list)))
    print("{} images inside geofence zone".format(len(geofence_list)))
    if len(duplicate_list)>0:
        os.makedirs(os.path.join(path, "duplicate"), exist_ok = True)
        move_to_subfolder(duplicate_list, os.path.join(path.path, "duplicate"))
    if len(geofence_list)>0:
        os.makedirs(os.path.join(path, "geofence"), exist_ok = True)
        move_to_subfolder(geofence_list, os.path.join(path.path, "geofence"))
    if len(reverse_list)>0:
        #print(reverse_list)
        write_josm_session([reverse_list], os.path.join(path.path, "session.jos"), [path.name + " | reverse"])
        open_session_in_josm(os.path.abspath(os.path.join(path.path, "session.jos")))
        
    
                  
if __name__ == '__main__':
    args=arg_parse()
    for _path in args.paths:
        if args.recursive:
            for sub_path in [f for f in os.scandir(_path) if f.is_dir()]:
                print("Path is: ", sub_path.path)
                main(sub_path)
        elif not args.recursive:
            print("Path is: ", sub_path.path)
            main(_path)

    print("End of Script")
	

