#
from __future__ import division
import datetime
import time
import sys
import argparse


def arg_parse():
    parser = argparse.ArgumentParser(description="Script to convert timestamp to datetime", version="0.1")
    parser.add_argument("source", nargs="?",
                        help="Path of log file which contains the timestamp")
    parser.add_argument("destination", help="File destination")
    

    args = parser.parse_args()
    print(args)
    return args



def convert_log(path_to_logfile):
    """Parse the log file generated by the raspberry pi, to keep only the shutters timestamps
    and the related informations
    :param path_to_logfile: path to the logfile
    :return: a list a log_infos namedtuple"""
    logfile = open(path_to_logfile, "r")
    loglist = []
    for line in logfile:
        line = line.replace("[", "")
        line = line.replace("]", "")
        line = line.replace("'", "")
        line = line.replace("(", "")
        line = line.replace(")", "")
        line = line.replace(" ", "")
        line = line.split(",")
        if "KTakepic" in line and not line[0].startswith("#"):
        
            shutter = datetime.datetime.fromtimestamp(float(line[0]))
                
            loglist.append((shutter.strftime("%Hh%Mm%S.") + (str(shutter.microsecond / 1000000))[2:], bin(int(line[2]))[2:].zfill(cam_count), int(line[3]), int(line[4])))

    logfile.close()
    return loglist

if __name__ == '__main__':
    args = arg_parse()
    cam_count = 4
    humanlog=convert_log(args.source)

    with open(args.destination, "w") as humanlogfile:
        for line in humanlog:
            humanlogfile.write(str(line)+"\n")
