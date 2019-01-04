# coding: utf8
#!/usr/bin/env python

import argparse
import datetime
import os
import math
import argparse
import csv
from exif_read import ExifRead as EXIFRead
from collections import namedtuple

Master_Picture_infos = namedtuple('Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', 'Latitude', 'Longitude', 'Ele', 'ImgDirection'])
Picture_infos = Master_Picture_infos(path=None, DateTimeOriginal=None, SubSecTimeOriginal=None, Latitude=None, Longitude=None, Ele=None, ImgDirection=None)


def arg_parse():
    parser = argparse.ArgumentParser(description="Script to scan a folder containing geolocalized jpg files, and write a csv file for the OpenPathView toolchain")
    parser.add_argument('-v', '--version', action='version', version='0.1')
    parser.add_argument("source", nargs="?",
                        help="Path source of the folders with the pictures. Without this parameter, "
                             "the script will use the current directory as the source", default=os.getcwd())
    parser.add_argument("--csv_name", help="output file's name", default = "PicturesInfos.csv")
    args = parser.parse_args()
    #print(args)
    return args

def get_image_list(path_to_pics):
        """
        Create a list of image tuples sorted by capture timestamp.
        @param directory: directory with JPEG files
        @return: a list of image tuples with time, directory, lat,long...
        :param path_to_pics:
        """
        print("Searching for jpeg images in ", path_to_pics, end=" ")
        file_list = []
        for root, sub_folders, files in os.walk(path_to_pics):
            file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]

        files = []
        # get DateTimeOriginal data from the images and sort the list by timestamp
        for filepath in file_list:
            #print(filepath)
            metadata = EXIFRead(filepath)
            try:
                t = metadata.extract_capture_time()
                s = int(t.microsecond / 1000000)
                geo = metadata.extract_geo()
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                ele = geo.get("altitude")
                direction = metadata.extract_direction()
                files.append(Picture_infos._replace(path=filepath, DateTimeOriginal = t, SubSecTimeOriginal = s,
                                                                Latitude = lat, Longitude = lon, Ele = ele, ImgDirection = direction))
                # print t
                # print type(t)
            except KeyError as e:
                # if any of the required tags are not set the image is not added to the list
                print("Skipping {0}: {1}".format(filepath, e))

        files.sort(key=lambda file: file.DateTimeOriginal)
        # print_list(files)
        
        
        print("{:5} found".format(len(files)))
        return files

def make_csv_line(pic):
    """
    Create a line with the required parameters for the OpenPathView toolchain
    datetime, lat, lon, alt, rad, goprofailed
    datetime : Sat Jul  8 17:40:50 2017
    lat, lon, alt : float
    rad : degree in degree minutes
    goprofailed : 0000 if the 4 cameras successfuly took the image
    separator : ;
    pic:Picture_infos namedtuple
    """

    date_time = str(pic.DateTimeOriginal.strftime("%a %b %d %H:%M:%S %Y"))
    lat = str(pic.Latitude)
    lon = str(pic.Longitude)
    ele = str(pic.Ele)
    #converting degree decimal to degree minutes
    degree = math.floor(pic.ImgDirection)
    minute = math.floor((pic.ImgDirection - degree)*60)
    rad = (str(degree) + "°" + " " + str(minute) + "'")
    
    line = (date_time, lat, lon, ele, rad, "0000")

    return line

def write_csv(lines, filename):
    with open(filename, "w", newline ='\n', encoding='utf-8') as csv_file:
        print("Writing {}".format(filename))
        header = ["time", "lat", "lon", "alt", "rad", "goProFailed"]
        csv_writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
        csv_writer.writerow(header)
        for line in lines:
            csv_writer.writerow(line)

def main():
    args = arg_parse()
    piclist = get_image_list(args.source)
    csv_lines = [make_csv_line(pic) for pic in piclist] 
    write_csv(csv_lines, args.csv_name)

if __name__ == "__main__":
    main()