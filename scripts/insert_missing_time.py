#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gpxpy
import gpxpy.gpx
import argparse


def arg_parse():
    """ Parse the command line you use to launch the script """
    parser = argparse.ArgumentParser(description="A tool to insert missing timestamp in gpx",
                                     version="0.01")

    parser.add_argument("gpx_file", help="Path to the gpx file")


    args = parser.parse_args()
    print(args)
    return args


args = arg_parse()
file = open(args.gpx_file, "r+")

gpx=gpxpy.parse(file)

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            if point.time == None:
                gpx.add_missing_times()
                print(point.time)

#create file
file.seek(0)
file.truncate()
file.write(gpx.to_xml())
file.close()
