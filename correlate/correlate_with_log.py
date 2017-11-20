#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function

import os, sys, datetime, time, argparse
import xml.etree.ElementTree as ET

from dateutil.tz import tzlocal
from lib.geo import interpolate_lat_lon, decimal_to_dms
from lib.gps_parser import get_lat_lon_time_from_gpx, get_lat_lon_time_from_nmea
from lib.exif import EXIF
from lib.exifedit import ExifEdit
from LatLon import LatLon, Latitude, Longitude
from geopy.distance import vincenty
from collections import namedtuple

Picture_infos = namedtuple('Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal'])
New_Picture_infos = namedtuple('New_Picture_infos',
                               ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', "New_DateTimeOriginal",
                                "New_SubSecTimeOriginal", "Longitude", "Latitude", "Ele", "ImgDirection"])
log_infos = namedtuple('log_infos',
                       ['log_timestamp', 'action', 'return_timestamp', 'time_to_answer', 'cam_return', 'pic_number', ])


# NOTE : modif dans lib.exifedit.py
# ajout de
# def add_subsec_time_original(self, subsec):
# """Add subsecond."""
# self.ef.exif.primary.ExtendedEXIF.SubSecTimeOriginal = subsec
# Voir si on ne peut pas récupérer directement la microsecond dans add_subsec_time_original
# et l'ajouter au tag SubSecTimeOriginal

# NOTE : modif de pexif.py 
# ajout de "ASCII" aux lignes 653 à 655

# TODO : Attention aux cas ou il manque le dernier log en cas de crash. !!!!!!!!!!

def list_images(directory):
    """
    Create a list of image tuples sorted by capture timestamp.
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
            files.append(Picture_infos(filepath, t, s))
            # print t
            # print type(t)
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filepath, e))

    files.sort(key=lambda file: file.DateTimeOriginal)
    # print_list(files)
    return files


def write_metadata(image_lists):
    """
    Write the exif metadata in the jpeg file
    :param image_lists : A list in list of New_Picture_infos namedtuple
    """
    for image_list in image_lists:
        for image in image_list:
            # metadata = pyexiv2.ImageMetadata(image.path)
            metadata = ExifEdit(image.path)
            # metadata.read()
            metadata.add_date_time_original(image.New_DateTimeOriginal)
            # metadata.add_subsec_time_original(image.New_SubSecTimeOriginal)
            metadata.add_lat_lon(image.Latitude, image.Longitude)
            metadata.add_direction(image.ImgDirection)
            if image.Ele is not None:
                metadata.add_altitude(image.Ele)
            metadata.write()
            print('Writing new timestamp to ', image.path)


def check_pic_count(log, image_list):
    """
    Count pic's number in the log, and count the real number of pics taken for each cam
    :param log: list of the logs stored in the raspberry Pi
    :param image_list: A list in list of Picture_infos namedtuple
    :return: list containing the results (cam1 pic count from log, cam1 pic, cam2 pic count from log.... )
    """
    pic_count = []
    print("pictures in the log vs pictures taken :")
    too_much_pictures = False
    for cam in range(cam_count):
        log_count = 0

        for log_line in log:
            if int(log_line.cam_return[0 - (cam + 1)]) == 1:
                log_count += 1
        pic_count.append(log_count)
        pic_count.append(len(image_list[cam]))
        # print("Camera {0} : {1} pictures in the log".format(cam + 1, pic_count[cam*2]))
        # print("Camera {0} : {1} pictures taken".format(cam + 1, pic_count[cam*2 +1]))
        print("Camera {0} : log/cam {1}/{2}".format(cam + 1, pic_count[cam * 2], pic_count[cam * 2 + 1]))

        if pic_count[cam * 2 + 1] > pic_count[cam * 2]:
            too_much_pictures = True
            print("1st log - 1st image :        {0} - {1}".format(log[0].log_timestamp,
                                                                  image_list[cam][0].DateTimeOriginal))
            print("2th log - 2th image :        {0} - {1}".format(log[1].log_timestamp,
                                                                  image_list[cam][1].DateTimeOriginal))
            print("...")
            print("last-1 log - last-1 image : {0} - {1}".format(log[-2].log_timestamp,
                                                                 image_list[cam][-2].DateTimeOriginal))
            print("last log - last image :       {0} - {1}".format(log[-1].log_timestamp,
                                                                   image_list[cam][-1].DateTimeOriginal))

    if too_much_pictures:
        print("Warning! There are more pictures than log records. You have to delete some pictures")
        sys.exit()

    return pic_count


def filter_images(piclists):
    """
    Filter the image lists to remove the "False" and "path=None" items
    :param piclists: A list of list of Picture_infos namedtuple
    :return: The same lists, but filtered
    """
    for i, piclist in enumerate(piclists):
        piclist = [j for j in piclist if type(j) != bool]
        piclist = [j for j in piclist if j.path is not None]
        piclists[i] = piclist

    return piclists


def correlate_nearest_time(loglist, piclist):
    """Try to find the right image for each log's timestamp.
    Find the closest image for each timestamp in the log.
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""

    # calcule le delta moyen log-pic sur les premiers 1% des photos
    delta_list = []
    try:

        for i, log_line in enumerate(loglist[:int(len(loglist) // 100 + 1)]):
            delta_list.append((log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds())
    except ZeroDivisionError:
        # print("except")
        delta_list.append((loglist[0].log_timestamp - piclist[0].DateTimeOriginal).total_seconds())
    # print(delta_list)
    avg_delta = sum(delta_list) / len(delta_list)
    print("ecart moyen entre le log et les photos : ", avg_delta)

    gap = 0
    piclist_corrected = []
    for i, pic in enumerate(piclist):
        n = 1
        # print("i, gap, n", i, gap, n)
        delta = abs((loglist[i + gap].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
        # print("loglist {0} et piclist {1}".format(i+gap, i))
        try:
            next_delta = abs((loglist[i + gap + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
            while next_delta <= delta:
                # print("delta  = ", delta)
                # print("delta2 = ", abs((loglist[i + gap + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta))
                delta = next_delta
                n = n + 1
                next_delta = abs(
                    (loglist[i + gap + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
        except:
            # print("End of list")
            pass

        new_datetimeoriginal = loglist[i + gap + n - 1].log_timestamp
        new_subsectimeoriginal = "%.6d" % (loglist[i + gap + n - 1].log_timestamp.microsecond)
        piclist_corrected.append(New_Picture_infos(pic.path, pic.DateTimeOriginal, pic.SubSecTimeOriginal,
                                                   new_datetimeoriginal, new_subsectimeoriginal, "", "", "", ""))

        for missing_pic in range(n - 1):
            piclist_corrected.insert(len(piclist_corrected) - 1, False)
            # display information
            print("=" * 30)
            print("Il manque une photo entre :")
            print(piclist[i - 1])
            print("et")
            print(piclist[i])
            print("-" * 30)
            # print("index de la photo : ", i)
            # print(loglist[i + gap + n - 3])
            # print(loglist[i + gap + n - 2])
            # print(loglist[i + gap + n - 1])
            # print("="*30)
            # add a gap to correlate the next pic with the correct log_timestamp
            gap += 1

    # piclist_corrected = [i for i in piclist_corrected if (type(i) == New_Picture_infos and type(i.path) != None) or type(i) == bool]
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    # print("standard deviation : ", deviation)
    return piclist_corrected, deviation


def correlate_double_diff_forward(loglist, piclist, pic_count_diff, cam_number):
    """Try to find the right image for each log's timestamp.
    Compute timedelta (from the beginning) between x+1 and x log's timestamp, timedelta between x+1 and x pic timestamp,
    and compute the timedelta between y pic timedelta and y log timedelta.
    The longest double difference timedelta will be used for the missing images.
    Then the timestamps from the log are copied to the images.
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :param pic_count_diff: how many images are missing
    :param cam_number: cam's number
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""

    # On va calculer le delta entre chaque déclenchement du log, et entre les photos
    # Calcul du delta entre les logs
    log_pic_delta = []
    for i, log_line in enumerate(loglist[:-1]):
        log_pic_delta.append((loglist[i + 1].log_timestamp - loglist[i].log_timestamp).total_seconds())

        # Calcul du delta entre les images
    pic_delta = []
    for i, pic_timestamp in enumerate(piclist[:-1]):
        # On calcule le delta entre 2 images prises par la caméra
        pic_delta.append((piclist[i + 1].DateTimeOriginal - piclist[i].DateTimeOriginal).total_seconds())

    # print("log_pic_delta : ", log_pic_delta)
    # print("pic_delta : ", pic_delta)
    # ========================================================================
    # Calcul du delta entre les delta, depuis le début vers la fin
    inter_delta = []
    for i, delta in enumerate(log_pic_delta):
        try:
            inter_delta.append(log_pic_delta[i] - pic_delta[i])
        except:
            # print("fin de liste")
            pass
    # print("inter_delta", inter_delta)
    # print(sorted(inter_delta))

    # Dans le cas où on a des variations de vitesse et des images manquantes, les inter_delta peuvent êtres
    # trompeur. On supprime ceux qui sont incorrectes, en faisant la division de la valeur max par la valeur min.
    # Si elle est < -1 il ne faut pas tenir compte de ces min max.
    # print("Max est : ", max(inter_delta))
    # print ("Min est : ", min(inter_delta))
    while max(inter_delta) / min(inter_delta) < -1:
        inter_delta[inter_delta.index(max(inter_delta))] = 0
        inter_delta[inter_delta.index(min(inter_delta))] = 0
        # print("On met a 0 inter_delta ", inter_delta.index(max(inter_delta)))
        # print("On met a 0 inter_delta ", inter_delta.index(min(inter_delta)))
    # print("inter_delta sans les bad max-min : ")
    # print(inter_delta)

    # Maintenant, on cherche la ou les valeurs max nécessaires
    idx = []
    for i in range(pic_count_diff):
        idx.append(inter_delta.index(min(inter_delta)))
        inter_delta[idx[i]] = 0
    print("=" * 30)
    print("idx ordre normal : ", idx)
    for i in idx:
        print()
        print("Il manque la photo entre :")
        print(piclist[i])
        print("et")
        print(piclist[i + 1], ".\n")
        print("=" * 30)

    # On trie la liste d'index pour éviter d'insérer au même endroit car
    # le fait d'insérer décale l'insertion suivante
    idx.sort()
    # On insère une "image vide" à "idx +1"

    for i, missing_pic in enumerate(idx):
        piclist.insert(missing_pic + i + 1, False)

    # C'est bon, on peut recopier les timestamps depuis le log
    piclist_corrected = []
    for i, log_line in enumerate(loglist):
        # print ("test int : ", int(log_line.cam_return[0 - (cam_number +1)]) == 1)
        # print ("test type : ", type(piclist[i]) == Picture_infos)
        # print("type est : ", type(piclist[i]))
        # print("retour de isinstance(piclist[i], Picture_infos): ", isinstance(piclist[i], Picture_infos))
        if type(piclist[i]) == Picture_infos:

            new_datetimeoriginal = log_line.log_timestamp
            new_subsectimeoriginal = "%.6d" % (log_line.log_timestamp.microsecond)
            piclist_corrected.append(New_Picture_infos(piclist[i].path,
                                                       piclist[i].DateTimeOriginal,
                                                       piclist[i].SubSecTimeOriginal,
                                                       new_datetimeoriginal,
                                                       new_subsectimeoriginal,
                                                       "", "", "", ""))
        elif type(piclist[i]) == bool:
            piclist_corrected.append(piclist[i])
    # print("piclist_corrected : ", piclist_corrected)
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))

    return piclist_corrected, deviation


def correlate_double_diff_backward(loglist, piclist, pic_count_diff, cam_number):
    """Try to find the right image for each log's timestamp.
    Compute timedelta (from the end) between x+1 and x log's timestamp, timedelta between x+1 and x pic timestamp,
    and compute the timedelta between y pic timedelta and y log timedelta.
    The longest double difference timedelta will be used for the missing images.
    Then the timestamps from the log are copied to the images.
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :param pic_count_diff: how many images are missing
    :param cam_number: cam's number
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""

    # On va calculer le delta entre chaque déclenchement du log, et entre les photos
    # Calcul du delta entre les logs
    log_pic_delta = []
    for i, log_line in enumerate(loglist[:-1]):
        log_pic_delta.append((loglist[i + 1].log_timestamp - loglist[i].log_timestamp).total_seconds())

        # Calcul du delta entre les images
    pic_delta = []
    for i, pic_timestamp in enumerate(piclist[:-1]):
        # On calcule le delta entre 2 images prises par la caméra
        pic_delta.append((piclist[i + 1].DateTimeOriginal - piclist[i].DateTimeOriginal).total_seconds())

    # print("log_pic_delta : ", log_pic_delta)
    # print("pic_delta : ", pic_delta)
    # ========================================================================
    # Calcul du delta entre les delta, depuis la fin vers le début
    inter_delta_reverse = []
    log_pic_delta_reversed = log_pic_delta[::-1]
    pic_delta_reversed = pic_delta[::-1]
    for i, delta in enumerate(log_pic_delta_reversed):
        try:
            inter_delta_reverse.append(log_pic_delta_reversed[i] - pic_delta_reversed[i])
        except:
            # print("fin de liste")
            pass
    # print("inter_delta_reverse")
    # print(inter_delta_reverse)
    # Dans le cas où on a des variations de vitesse et des images manquantes, les inter_delta peuvent êtres
    # trompeur. On supprime ceux qui sont incorrectes, en faisant la division de la valeur max par la valeur min.
    # Si elle est < -1 il ne faut pas tenir compte de ces min max.
    # print("Max reverse est : ", max(inter_delta_reverse))
    # print ("Min reverse est : ", min(inter_delta_reverse))
    while max(inter_delta_reverse) / min(inter_delta_reverse) < -1:
        inter_delta_reverse[inter_delta_reverse.index(max(inter_delta_reverse))] = 0
        inter_delta_reverse[inter_delta_reverse.index(min(inter_delta_reverse))] = 0
        # print("On met a 0 inter_delta_reverse ", inter_delta_reverse.index(max(inter_delta_reverse)))
        # print("On met a 0 inter_delta_reverse ", inter_delta_reverse.index(min(inter_delta_reverse)))
    # print("inter_delta_reverse sans les bad max-min", inter_delta_reverse)

    idx = []
    for i in range(pic_count_diff):
        idx.append(inter_delta_reverse.index(min(inter_delta_reverse)))
        inter_delta_reverse[idx[i]] = 0
    print("=" * 30)
    print("idx ordre inverse : ", idx)
    for i in idx:
        print("Il manque la photo entre :")
        print(piclist[-(i + 2)])
        print("et")
        print(piclist[-(i + 1)])
        print("=" * 30)

    # On trie la liste d'index pour éviter d'insérer au même endroit car
    # le fait d'insérer décale l'insertion suivante

    idx.sort(reverse=True)
    # On insère une "image vide" à "idx-1"

    for missing_pic in idx:
        piclist.insert(len(piclist) - missing_pic - 1, False)
        # print("On insert un False à ", len(piclist)-missing_pic-1)
        # print(piclist[len(piclist)-missing_pic-1])
        # print(piclist[len(piclist)-missing_pic-2])

    # C'est bon, on peut recopier les timestamps depuis le log

    # debug
    # for pic in piclist[40:60]:
    #   print(pic)

    piclist_corrected = []
    for i, log_line in enumerate(loglist):
        if int(log_line.cam_return[0 - (cam_number + 1)]) == 1 and type(piclist[i]) == Picture_infos:
            new_datetimeoriginal = log_line.log_timestamp
            new_subsectimeoriginal = "%.6d" % (log_line.log_timestamp.microsecond)
            piclist_corrected.append(New_Picture_infos(piclist[i].path,
                                                       piclist[i].DateTimeOriginal,
                                                       piclist[i].SubSecTimeOriginal,
                                                       new_datetimeoriginal,
                                                       new_subsectimeoriginal,
                                                       "", "", "", ""))
        elif type(piclist[i]) == bool:
            piclist_corrected.append(piclist[i])

    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    # print("standard deviation : ", deviation)
    return piclist_corrected, deviation


def insert_missing_timestamp(loglist, piclists, cam):
    """Insert missing timestamp in the piclists, when the log indicate that the cam didn't answer to the shutter request
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :param cam: cam's number
    :return: the list of Picture_infos namedtuple with the missing timestamp inserted
    """
    # On insert les timestamps qu'on sait manquants (caméra qui n'ont pas répondu, donc 0 dans le log).
    # Cela évite de fausser les calculs des différences de temps entre chaque images
    new_piclists = []
    gap = 0
    for i, log_line in enumerate(loglist):
        if int(log_line.cam_return[0 - (cam + 1)]) == 1:
            try:
                new_piclists.append(piclists[cam][i - gap])
                # print("Ajout en position {0} de {1}".format(i, piclists[cam][i]))
            except:
                # print("End of list")
                pass

        elif int(log_line.cam_return[0 - (cam + 1)]) == 0:
            try:
                new_piclists.append(Picture_infos(None, log_line.log_timestamp, 0))
                gap += 1
                # print("Ajout en position {0} de {1}".format(i, Picture_infos(None, log_line.log_timestamp, 0)))
            except:
                # print("End of list")
                pass
    return new_piclists


def correlate_log_and_pic(loglist, image_list, pic_count):
    """Correlate the images timestamp with the log timestamps.
    If there are more log's timestamps than pic'count, 3 different algorithms will try to find
    which timestamp has no image related to the it.

    :param loglist: a list of log_infos nametuple
    :param image_list: a list of of list of Picture_infos namedtuple
    :param pic_count: log and cam pic count
    :return: a new list of list of New_Picture_infos namedtuple with the more accurate timestamps.
    """
    piclists_corrected = []
    for cam in range(cam_count):

        single_cam_image_list = insert_missing_timestamp(loglist, image_list, cam)
        pic_count_diff = pic_count[cam * 2] - pic_count[cam * 2 + 1]
        original_deviation = standard_deviation(compute_delta3(loglist, single_cam_image_list))

        if pic_count_diff == 0:
            print("Camera {0} : Exact correlation between logfile and pictures".format(cam + 1))
            for i, log_line in enumerate(loglist):
                if int(log_line.cam_return[0 - (cam + 1)]) == 1:
                    new_datetimeoriginal = log_line.log_timestamp
                    new_subsectimeoriginal = "%.6d" % (log_line.log_timestamp.microsecond)
                    # single_cam_image_list[i] = single_cam_image_list[i]._replace(New_DateTimeOriginal=new_datetimeoriginal, New_SubSecTimeOriginal=new_subsectimeoriginal)
                    single_cam_image_list[i] = New_Picture_infos(single_cam_image_list[i].path,
                                                                 single_cam_image_list[i].DateTimeOriginal,
                                                                 single_cam_image_list[i].SubSecTimeOriginal,
                                                                 new_datetimeoriginal, new_subsectimeoriginal, "", "",
                                                                 "", "")

            deviation = standard_deviation(compute_delta3(loglist, image_list[cam]))
            print("standard deviation after correction: ", deviation)

            piclists_corrected.append(single_cam_image_list)


        elif pic_count_diff > 0:
            print("=" * 80)
            print("Camera {0} : {1} Missing pictures".format(cam + 1, pic_count_diff))

            # On utilise plusieurs algorithmes différents pour retrouver les images manquantes
            forward = correlate_double_diff_forward(loglist, single_cam_image_list[:], pic_count_diff, cam)
            backward = correlate_double_diff_backward(loglist, single_cam_image_list[:], pic_count_diff, cam)
            nearest = correlate_nearest_time(loglist, single_cam_image_list[:])
            print("Time deviation before correction : ", original_deviation)
            print("double diff forward deviation: ", forward[1])
            print("double diff backward deviation: ", backward[1])
            print("nearest time deviation: ", nearest[1])

            user_input = raw_input("Quel algo ? 1, 2 ou 3 ? ")
            if int(user_input) == 1:
                piclists_corrected.append(forward[0])
            elif int(user_input) == 2:
                piclists_corrected.append(backward[0])
            elif int(user_input) == 3:
                piclists_corrected.append(nearest[0])
            else:
                print("Invalid choice")

                # TODO coder un while pour le cas d'une mauvaise réponse

        elif pic_count_diff < 0:
            print("BORDEL !! PAS ENCORE FAIT !!")

    return piclists_corrected


def compute_delta(mylist):
    delta = []
    for i, timestamp in enumerate(mylist[:-1]):
        # On calcule le delta entre 2 images prises par la caméra
        try:
            delta.append((mylist[i + 1].DateTimeOriginal - mylist[i].DateTimeOriginal).total_seconds())
        except:
            print("une erreur de valeur")
    return delta


def compute_delta2(piclist1, piclist2):
    delta = []
    for i, line in enumerate(piclist1):
        try:
            delta.append((piclist1[i].DateTimeOriginal - piclist2[i].DateTimeOriginal).total_seconds())
        except:
            print("Impossible de calculer le delta")
    print("somme des deltas : ", sum(delta))
    return delta


def compute_delta3(loglist1, piclist2):
    delta = []
    # print("loglist1 : ", loglist1)
    # print("piclist2 : ", piclist2)
    for i, line in enumerate(loglist1):
        try:
            delta.append((loglist1[i].log_timestamp - piclist2[i].DateTimeOriginal).total_seconds())
        except:
            None
            # print("Impossible de calculer le delta")
    # print("somme des deltas : ", sum(delta))
    return delta


def standard_deviation(list1):
    """Calculate a standard deviation
    :param list1: list of values
    :return: standard deviation value"""
    # moyenne
    moy = sum(list1, 0.0) / len(list1)
    # variance
    variance = [(x - moy) ** 2 for x in list1]
    variance = sum(variance, 0.0) / len(variance)
    # ecart_type
    deviation = variance ** 0.5
    return deviation


def parse_log(path_to_logfile):
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
        if "KTakepic" in line:
            try:
                loglist.append(log_infos(datetime.datetime.fromtimestamp(float(line[0])), line[1],
                                         datetime.datetime.fromtimestamp(float(line[5])), int(line[3]), line[6][2:],
                                         int(line[4])))

            except:
                print("parse error")
    logfile.close()
    return loglist


def geotag_from_gpx(piclists, gpx_file, offset_time=0, offset_bearings=0, offset_distance=0):
    """This function will try to find the location (lat lon) for each pictures in each list, compute the direction
    of the pictures with an offset if given, and offset the location with a distance if given. Then, these
    coordinates will be added in the New_Picture_infos namedtuple.
    :param piclists: a list of of list of New_Picture_infos namedtuple
    :param gpx_file: a gpx or nmea file path
    :param offset_time: time offset between the gpx/nmea file, and the image's timestamp
    :param offset_bearings: the offset angle to add to the direction of the images (for side camera)
    :param offset_distance: a distance (in meter) to move the image from the computed location. (Use this setting to
    not have all the images from a multicam setup at the same exact location
    :return: nothing, the function update the New_Picture_infos namedtuple inside the lists"""
    now = datetime.datetime.now(tzlocal())
    print("Your local timezone is {0}, if this is not correct, your geotags will be wrong.".format(
        now.strftime('%Y-%m-%d %H:%M:%S %z')))

    # read gpx file to get track locations
    if gpx_file.lower().endswith(".gpx"):
        gpx = get_lat_lon_time_from_gpx(gpx_file)
    elif gpx_file.lower().endswith(".nmea"):
        gpx = get_lat_lon_time_from_nmea(gpx_file)
    else:
        print("\nWrong gnss file! It should be a .gpx or .nmea file.")
        sys.exit()

    for piclist, offset_bearing in zip(piclists, offset_bearings):

        start_time = time.time()
        print("===\nStarting geotagging of {0} images using {1}.\n===".format(len(piclist), gpx_file))

        # for filepath, filetime in zip(piclist.path, piclist.New_DateTimeOriginal):
        for i, pic in enumerate(piclist):
            # add_exif_using_timestamp(filepath, filetime, gpx, time_offset, bearing_offset)
            # metadata = ExifEdit(filename)
            t = pic.New_DateTimeOriginal - datetime.timedelta(seconds=offset_time)
            try:
                lat, lon, bearing, elevation = interpolate_lat_lon(gpx, t)
                corrected_bearing = (bearing + offset_bearing) % 360
                # Apply offset to the coordinates if distance_offset exists
                if offset_distance != 0:
                    new_Coords = LatLon(lat, lon).offset(corrected_bearing, offset_distance / 1000)
                    lat = new_Coords.lat.decimal_degree
                    lon = new_Coords.lon.decimal_degree
                # Add coordinates, elevation and bearing to the New_Picture_infos namedtuple
                piclist[i] = pic._replace(Longitude=lon, Latitude=lat, Ele=elevation, ImgDirection=corrected_bearing)

            except ValueError, e:
                print("Skipping {0}: {1}".format(pic.path, e))

        print("Done geotagging {0} images in {1:.1f} seconds.".format(len(piclist), time.time() - start_time))

def move_too_close_pic(piclists, min_distance):
    """Move pictures to another folder is they're too close to each other. Useful to remove duplicate pictures
    :param piclists: a list of of list of New_Picture_infos namedtuple
    :param min_distance: the minimum distance between two pictures. If the distance between pic1 and pic2 is smaller,
    pic2 will be move to the "excluded" folder"""
    
    def move_pic(full_path_pic):
        """Move the picture"""
        destination = os.path.join(os.path.dirname(full_path_pic), "excluded")
        if not os.path.exists(destination):
            try:
                os.makedirs(destination)
            except:
                print("Error! Can't create destination directory {0}".format(destination))
                os.exit()
        print("Moving {0} to {1}".format(os.path.basename(full_path_pic), destination))
        return os.rename(full_path_pic, os.path.join(destination, os.path.basename(full_path_pic)))
    
    for piclist in piclists:
        dist_since_start = 0
        for i, pic in enumerate(piclist):
            try:
                next_pic = piclist[i+1]
                distance = vincenty((next_pic.Latitude, next_pic.Longitude), (pic.Latitude, pic.Longitude)).meters
                distance = distance + dist_since_start
                if distance < min_distance:
                    # print("distance = ", distance)
                    move_pic(pic.path)
                else:
                    dist_since_start = 0
                    
            except:
                pass
                

def write_josm_session(piclists, session_file_path, cam_names, gpx_file=None):
    """
    Build a josm session file in xml format with all the pictures on separate layer, and another
    layer for the gpx/nmea file
    :param piclists: a list of of list of New_Picture_infos namedtuple
    :param session_file_path: the path and name of the session file
    :param cam_names: The camera's name, which will be the layer's name
    :param gpx_file: The path of the gpx/nmea file.
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
            geoimage = ET.SubElement(layer, "geoimage")
            g_file = ET.SubElement(geoimage, "file")
            g_file.text = pic.path
            g_thumb = ET.SubElement(geoimage, "thumbnail")
            g_thumb.text = "false"
            g_position = ET.SubElement(geoimage, "position")
            g_position.attrib = {"lat": str(pic.Latitude), "lon": str(pic.Longitude)}
            g_elevation = ET.SubElement(geoimage, "elevation")
            g_elevation.text = str(pic.Ele)
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
            g_exif_time.text = str(int(time.mktime(pic.New_DateTimeOriginal.timetuple()))) + "%.3d" % round(
                pic.New_DateTimeOriginal.microsecond / float(1000), 0)
            g_exif_direction = ET.SubElement(geoimage, "exif-image-direction")
            g_exif_direction.text = str(pic.ImgDirection)
            g_is_new_gps = ET.SubElement(geoimage, "is-new-gps-data")
            g_is_new_gps.text = "true"

    if gpx_file is not None:
        gpx_layer = ET.SubElement(layers, "layer")
        gpx_layer.attrib = {"index": str(len(piclists) + 1), "name": gpx_file.split("\\")[-1], "type": "tracks",
                            "version": "0.1", "visible": "true"}
        gpx_file_layer = ET.SubElement(gpx_layer, "file")
        gpx_file_layer.text = "file:/" + gpx_file.replace("\\", "/")

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
    import urllib2, posixpath

    if os.sep != posixpath.sep:
        session_file_path = session_file_path.replace(os.sep, posixpath.sep)

    print("Opening the session in Josm....", end="")
    r = urllib2.urlopen("http://127.0.0.1:" + remote_port + "/open_file?filename=" + session_file_path)
    answer = r.read()
    print("Success!") if "OK" in answer else print("Error!")
    r.close()


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
    parser.add_argument("source", nargs="?",
                        help="Path source of the folders with the pictures. Without this parameter, "
                             "the script will use the current directory as the source", default=os.getcwd())
    parser.add_argument("profile", help="Profile's name of the multicam settings", default="v4mbike")
    parser.add_argument("-l", "--logfile", help="Path to the log file. Without this parameter, "
                                                "the script will search in the current directory")
    parser.add_argument("-g", "--gpxfile", help="Path to the gpx/nmea file. Without this parameter, "
                                                "the script will search in the current directory")
    parser.add_argument("-t", "--time_offset",
                        help="Time offset between GPX and photos. If your camera is ahead by one minute, time_offset is 60.",
                        default=0, type=float)
    parser.add_argument("-j", "--josm", help="Load the pictures in Josm (must be running)", action="store_true")
    parser.add_argument("-w", "--write_exif", help="Write the new exif tags in the images", action="store_true")
    parser.add_argument("-x", "--exclude_close_pic", help="Move the too close pictures to the exluded folder", action="store_true")

    args = parser.parse_args()
    print(args)
    return args


def config_parse(profile_name):
    """Parse the profile entered with the command line. This profile is in the profile.cfg file.
    These parameters are used to automate the processing
    :param profile_name: Profile's name"""

    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read(os.path.dirname(sys.argv[0]) + "\\profile.cfg")

    folder_string = config.get(profile_name, "folder_names")
    folder_string = [i.strip() for i in folder_string.split(",")]

    cam_names = config.get(profile_name, "cam_names")
    cam_names = [i.strip() for i in cam_names.split(",")]

    cam_bearing = config.get(profile_name, "cam_bearing")
    cam_bearing = [int(i.strip()) for i in cam_bearing.split(",")]

    distance_from_center = float(config.get(profile_name, "distance_from_center"))
    
    min_pic_distance = float(config.get(profile_name, "min_pic_distance"))

    return folder_string, cam_names, cam_bearing, distance_from_center, min_pic_distance


def find_file(directory, file_extension):
    """Try to find the files with the given extension in a directory
    :param directory: the directory to look in
    :param file_extension: the extension (.jpg, .gpx, ...)
    :return: a list containing the files found in the directory"""
    file_list = []
    for root, sub_folders, files in os.walk(directory):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(file_extension)]

    if len(file_list) == 1:
        file = file_list[0]
        print("{0} : {1} will be used in the script".format(file_extension, file))
    elif len(file_list) > 1:
        file = file_list[0]
        print("Warning, more than one {0} file found".format(file_extension))
        print("{0} : {1} will be used in the script".format(file_extension, file))
    elif len(file_list) == 0:
        file = None
        print("Warning, no {0} file found".format(file_extension))

    return file


def find_directory(working_dir, strings_to_find):
    """Try to find the folders containing a given string in their names
    :param working_dir: The base folder to search in
    :param strings_to_find: a list of strings to find in the folder's names
    :return: a list of folder with the string_to_find in their name"""
    images_path = []
    dir_list = [i for i in os.listdir(working_dir) if os.path.isdir(i)]
    for string in strings_to_find:
        try:
            images_path.append(os.path.abspath(os.path.join(working_dir, dir_list[dir_list.index(string)])))
        except ValueError:
            print("I can't find {0}".format(string))
            sys.exit()
    return images_path


if __name__ == '__main__':
    # Parsing the command line arguments
    args = arg_parse()

    # Trying to find the logfile in the working directory if none is given in the command line
    if args.logfile is None:
        print("=" * 30)
        args.logfile = find_file(args.source, "log")
        # TODO raise an exception if find_file return none

    # Trying to find a nmea file in the working directory if none is given in the command line
    if args.gpxfile is None:
        print("=" * 30)
        args.gpxfile = find_file(args.source, "nmea")
    # Or a gpx file if there is no nmea file
    if args.gpxfile is None:
        args.gpxfile = find_file(args.source, "gpx")
    # TODO raise an exception if args.gpxfile is None

    #Parsing the multicam profile
    folder_string, cam_names, cam_bearings, distances_from_center, min_pic_distance = config_parse(args.profile)

    # Trying to find the folders containing the pictures
    path_to_pics = find_directory(args.source, folder_string)

    # Searching for all the jpeg images
    image_list = []
    print("=" * 80)
    print("Searching for jpeg images in ... ")
    for path in path_to_pics:
        print(path)
        image_list.append(list_images(path))

    # Counting how many cameras are used
    cam_count = len(image_list)

    # Parsing the logfile
    loglist = parse_log(args.logfile)

    # Counting the shutter requests stored in the logfile, and compare with the images count.
    print("=" * 80)
    pic_count = check_pic_count(loglist, image_list)

    #   for cam in range(cam_count):
    #      image_list[cam] = insert_missing_timestamp(loglist, image_list, cam)

    # Trying to correlate the shutter's timestamps with the images timestamps.
    piclists_corrected = correlate_log_and_pic(loglist, image_list, pic_count)
    # Remove the unuseful value in the lists
    piclists_corrected = filter_images(piclists_corrected)

    # Geotag the pictures, add the direction, and offset them from the location
    print("=" * 80)
    geotag_from_gpx(piclists_corrected, args.gpxfile, args.time_offset, cam_bearings, distances_from_center)
    print("=" * 80)

    # Write a josm session file to check the picture's location before writing the new exif data
    if args.josm:
        session_file_path = os.path.abspath(os.path.join(args.source, "session.jos"))
        write_josm_session(piclists_corrected, session_file_path, cam_names, args.gpxfile)
        open_session_in_josm(session_file_path)

    # Write the new exif data in the pictures.
    print("=" * 80)
    if args.write_exif:
        user_input = raw_input("Write the new exif data in the pictures? (y or n) : ")
        if user_input == "y":
            write_metadata(piclists_corrected)
    # Move the duplicate pictures to the excluded folder
    if args.exclude_close_pic:
        print("Moving pictures too close to each other")
        move_too_close_pic(piclists_corrected, min_pic_distance)
print("End of correlation")



# 2) Count pictures in logfile, and compare with the pictures count for each cam, (and print it in case of large disparity)
# function check_pic_count

# pic_count = check_pic_count(loglist, image_list)

# 2b) Print time delta between log and cameras for the first pic, and the last one  <=== il vaudrait mieux l'afficher une fois la corrélation faite, et avant de remplacer les timestamp


# 3) Correlate
# 3a) nbr de pic ds log xyz = nbr de pic pour les cam xyz


# Pour aider à repérer les changements de vitesse qui perturbent la détection des photos manquantes, on peut ajouter à la fin de loglist et de image_list :
# image_list[0].append(Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\BLAAAA', DateTimeOriginal=datetime.datetime(2017, 10, 7, 17, 51, 1, 315055), SubSecTimeOriginal='315055'))
# loglist.append(log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 17, 51, 1, 315055), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 17, 51, 1, 315055), time_to_answer=3000, cam_return='1101', pic_number=2638))




# 4) geolocalize and add direction to the pictures

# 4b) create the 360° pictures
# 5) Open the pictures in Josm
