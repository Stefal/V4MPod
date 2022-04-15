#!/usr/bin/env python
# -*- coding: utf-8 -*-



import argparse
import datetime
import os
import sys
import time
import pyproj
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import logging
import xml.etree.ElementTree as ET
from builtins import input
from collections import namedtuple

from dateutil.tz import tzlocal
from lib.exif_read import ExifRead as EXIF
from lib.exif_write import ExifEdit
from lib.geo import interpolate_lat_lon
from lib.gps_parser import get_lat_lon_time_from_gpx, get_lat_lon_time_from_nmea

logfile_name = "correlate.log"
# source for logging : http://sametmax.com/ecrire-des-logs-en-python/
# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger()
# on met le niveau du logger à DEBUG, comme ça il écrit tout
logger.setLevel(logging.INFO)
 
# création d'un formateur qui va ajouter le temps, le niveau
# de chaque message quand on écrira un message dans le log
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
# création d'un handler qui va rediriger une écriture du log vers
# un fichier
file_handler = logging.FileHandler(logfile_name, 'w')
# on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
# créé précédement et on ajoute ce handler au logger
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
 
# création d'un second handler qui va rediriger chaque écriture de log
# sur la console
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

Master_Picture_infos = namedtuple('Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', 'Latitude', 'Longitude', 'Ele'])
Picture_infos = Master_Picture_infos(path=None, DateTimeOriginal=None, SubSecTimeOriginal=None, Latitude=None, Longitude=None, Ele=None)
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

# NOTE : correction du bug de lecture des microseconds dans EXIF
#
#
# NOTE : modif de pexif.py 
# ajout de "ASCII" aux lignes 653 à 655

# TODO : pour le calcul du delta moyen sur les x premières photos, peut-être ignorer la ou les premières.


class Cam_Infos:
    def __init__(self, name, dir_source, bearing, distance_from_center, logpos, log = None):
        self.name = name
        self.source_dir = dir_source
        self.bearing = bearing
        self.distance_from_center = distance_from_center
        self.log_pos = logpos
        self.log_list = log
        self.image_list = None
        self.new_image_list = None
        self.log_count = None
        self.pic_count = None
        
    def add_log(self,loglist):
        self.log_count = 0
        self.log_list = []
        for i, log_line in enumerate(loglist):
            this_cam_return = True if int(log_line.cam_return[0 - (self.log_pos + 1)]) == 1 else False
            self.log_list.append(log_infos(log_line.log_timestamp,
                                                log_line.action,
                                                log_line.return_timestamp,
                                                log_line.time_to_answer,
                                                this_cam_return,
                                                log_line.pic_number))
                                                
            if this_cam_return is True:
                self.log_count += 1

    def get_image_list(self, path_to_pics):
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
            metadata = EXIF(filepath)
            try:
                t = metadata.extract_capture_time()
                s = int(t.microsecond / 1000000)
                files.append(Picture_infos._replace(path=filepath, DateTimeOriginal = t, SubSecTimeOriginal = s))
                # print t
                # print type(t)
            except KeyError as e:
                # if any of the required tags are not set the image is not added to the list
                print("Skipping {0}: {1}".format(filepath, e))

        files.sort(key=lambda file: file.DateTimeOriginal)
        # print_list(files)
        
        self.image_list = files
        self.pic_count = len(self.image_list)
        print("{:5} found".format(self.pic_count))
        
    
    def check_pic_count(self):
        """
        TODO revoir docstring
        Count pic's number in the log, and count the real number of pics taken for each cam
        :return: list containing the results (cam1 pic count from log, cam1 pic, cam2 pic count from log.... )
        """
        
        print("pictures in the log vs pictures taken :")

        self.log_count = 0
        #TODO peut mieux faire
        for log_line in self.loglist:
            if log_line.cam_return == 1:
                self.log_count += 1
                
        
        # print("Camera {0} : {1} pictures in the log".format(cam + 1, pic_count[cam*2]))
        # print("Camera {0} : {1} pictures taken".format(cam + 1, pic_count[cam*2 +1]))
        print("Camera {0} : log/cam {1}/{2}".format(self.name, self.log_count, self.pic_count))

        if self.pic_count > self.log_count:
            print("1st log - 1st image :        {0} - {1}".format(self.log_list[0].log_timestamp,
                                                                  self.image_list[0].DateTimeOriginal))
            print("2th log - 2th image :        {0} - {1}".format(self.log_list[1].log_timestamp,
                                                                  self.image_list[1].DateTimeOriginal))
            print("...")
            print("last-1 log - last-1 image : {0} - {1}".format(self.log_list[-2].log_timestamp,
                                                                 self.image_list[-2].DateTimeOriginal))
            print("last log - last image :       {0} - {1}".format(self.log_list[-1].log_timestamp,
                                                                   self.image_list[-1].DateTimeOriginal))

    def filter_images(self):
        """
        Filter the new_image list to remove the "False" and "path=None" items
        """
        #TODO vérfier pourquoi j'ai du False et du None. Peut-être tout basculer
        #sur la même valeur None OU False.
        piclist = [j for j in self.new_image_list if isinstance(j, New_Picture_infos)]
        piclist = [j for j in piclist if j.path is not None]
        self.new_image_list = piclist

    def filter_no_latlon(self):
        """
        Filter the new_image_list to remove the pictures without lat/long data
        """
        piclist = [j for j in self.new_image_list if j.Latitude]
        self.new_image_list = piclist
        
class Cam_Group(list):
    def __init__(self, cam_list=[], name=None):
        self.name = name
        list.__init__(self, cam_list)
        
    def __repr__(self):
        for cam in self:
            print("{} - bearing: {} - pics: {}".format(cam.name, cam.bearing, cam.pic_count))
            
    def __getattr__(self, cam_count):
        return len(self)
        
    def add_log(self, loglist):
        for cam in self:
            cam.add_log(loglist)
            
    def get_image_list(self):
        for cam in self:
            cam.get_image_list(cam.source_dir)
        
    def filter_images(self, data=False, latlon=False):
        if data:
            for cam in self:
                cam.filter_images()
        if latlon:
            for cam in self:
                cam.filter_no_latlon()

                
class BraceMessage(object):
    """This class here to use the new-style formating inside the logger. More details here :
    https://docs.python.org/3/howto/logging-cookbook.html#formatting-styles
    """
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)

__ = BraceMessage

def list_geoimages(directory):
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


def write_metadata(image_lists):
    """
    Write the exif metadata in the jpeg file
    :param image_lists : A list in list of New_Picture_infos namedtuple
    """
    for image_list in image_lists:
        for image in image_list:
            #TODO dans ces if, chercher pourquoi j'ai '' comme valeur, au lieu de None, ce qui
            #rendrait la condition plus lisible (if image.Latitude is not None:)
            # metadata = pyexiv2.ImageMetadata(image.path)
            metadata = ExifEdit(image.path)
            # metadata.read()
            metadata.add_date_time_original(image.New_DateTimeOriginal)
            # metadata.add_subsec_time_original(image.New_SubSecTimeOriginal)
            
            if image.Latitude != "" and image.Longitude != "":
                #import pdb; pdb.set_trace()
                metadata.add_lat_lon(image.Latitude, image.Longitude)
                
            if image.ImgDirection != "":
                metadata.add_direction(image.ImgDirection)
                
            if image.Ele != "" and image.Ele is not None:
                metadata.add_altitude(image.Ele)
            metadata.write()
            print('Writing new Exif metadata to ', image.path)


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




def correlate_nearest_time_exclusive(camera_obj, loglist = None, piclist = None, user_delta = True):
    """Try to find the right image for each log's timestamp.
    Find the closest image for each timestamp in the log.
    :param user_delta:
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""

    # calcule le delta moyen log-pic sur les premiers 10% des photos
    if loglist == None : loglist = camera_obj.log_list
    if piclist == None : piclist = camera_obj.image_list
    piclist = manual_timestamp(camera_obj, loglist, piclist)
    delta_list = []
    try:

        for i, log_line in enumerate(loglist[:int(len(loglist) // 10 + 1)]):
            if piclist[i].path is not None:
                delta_list.append((log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds())
            print("{0} : calcul {1} - {2} : {3}".format(i, log_line.log_timestamp, piclist[i].DateTimeOriginal, (log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds()))
    except ZeroDivisionError:
        # print("except")
        delta_list.append((loglist[0].log_timestamp - piclist[0].DateTimeOriginal).total_seconds())
    # print(delta_list)
    #import pdb; pdb.set_trace()
    try:
        avg_delta = sum(delta_list) / len(delta_list)
    except ZeroDivisionError:
        avg_delta = -0.5
    
    print("ecart moyen entre le log et les photos : ", avg_delta)
    if user_delta:
        user_delta = input("Enter a new delta value: ")
        if user_delta is not None and len(user_delta) != 0:
            avg_delta = float(user_delta)
    
    gap = 0
    piclist_corrected = []
    logger.info(__("len loglist:{0}".format(len(loglist))))
    logger.info(__("len piclist:{0}".format(len(piclist))))
    logger.info(__("avg delta = {0}".format(avg_delta)))
    #We will use a loglist copy as we will modify it
    cp_loglist = loglist[:]
    backup_delta = avg_delta
    for i, pic in enumerate(piclist):
        standby_delay = 0
        n = 1
        #print("i, gap, n", i, gap, n)
        #delta = abs((loglist[i + gap].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
        #print("loglist {0} et piclist {1}".format(i+gap + n, i))
        #if len(piclist_corrected) > 0 and piclist_corrected[-1].new_datetimeoriginal >= log
        try:
        
            #Si le chemin de l'image suivant celle en cours de calcul est None, 
            # alors c'est une image virtuelle qui a été ajoutée pour recaler.
            #Dans ce cas, son timestamp est forcément bon, alors on force celle en cours à la position actuelle
            # en assignant une valeur de 0 à delta. Si on ne le faisait pas, avg_delta pourrait décaler l'image en cours
            # à la place de l'image virtuelle.
            if  i + 1 < len(piclist) and piclist[i+1].path is None:
                delta = 0
                next_delta = 1
                logger.info("l'image suivante est une Image virtuelle.")
            else:
                #S'il s'est passé plus de 60 secondes entre la dernière photo et celle en cours, alors les caméras se sont mise
                #en veille, ce qui fait que celle en cours aura un timestamp un peu retardé par rapport aux suivantes.
                #Pour cette raison, on ajout 0.8s pour éviter que la photo soit calé sur le timestamp suivant.
                #Le try except est là pour éviter l'erreur pour la toute première photo.
                try:
                    standby_delay = 0.8 if (pic.DateTimeOriginal - piclist[i-1].DateTimeOriginal).total_seconds() > 50 else 0
                    
                    if standby_delay != 0:
                        logger.info(__("standby_delay vaut {}".format(standby_delay)))
                except IndexError:
                    #TODO la première photo sera en retard uniquement si la cam a eu le temps de se mettre en veille depuis son
                    # démarrage
                    logger.info("première photo, elle sera un peu en retard")
                    standby_delay = 0.8

                short_path = os.path.basename(pic.path) if pic.path is not None else "virtual image"
                delta = abs((cp_loglist[i + gap].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta + standby_delay)
                logger.info(__("A Calcul de la diff entre {0} et {1} : {2}".format(cp_loglist[i + gap].log_timestamp, short_path, delta)))
                
                # gestion du cas de la dernière photo
                if i + gap + n < len(cp_loglist):
                    next_delta = abs((cp_loglist[i + gap + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta + standby_delay)
                    logger.info(__("B Calcul de la diff entre {0} et {1} : {2}".format(cp_loglist[i + gap + n].log_timestamp, short_path, next_delta)))
                else:
                    delta = 0
                    logger.info("Fin de la liste")
                    
                
            while next_delta <= delta:
                piclist_corrected.insert(len(piclist_corrected), None)
                delta = next_delta
                n = n + 1
                next_delta = abs(
                    (cp_loglist[i +  gap + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta + standby_delay)
                logger.info("="*10)
                logger.info(__("delta  = {0} pour loglist {1} et piclist {2}".format(delta, cp_loglist[i + gap + n - 1].log_timestamp, os.path.basename(pic.path))))
                logger.info(__("delta2 = {0} pour loglist {1} et piclist {2}".format(next_delta, cp_loglist[i + gap + n].log_timestamp, os.path.basename(pic.path))))
                    
            new_datetimeoriginal = cp_loglist[i + gap + n - 1].log_timestamp
            new_subsectimeoriginal = "%.6d" % (cp_loglist[i + gap + n - 1].log_timestamp.microsecond)
            piclist_corrected.append(New_Picture_infos(pic.path, pic.DateTimeOriginal, pic.SubSecTimeOriginal,
                                                   new_datetimeoriginal, new_subsectimeoriginal, "", "", "", ""))
                                                   
            if pic.path is not None:
                logger.info(__(">>>>Association de log {0} avec pic {1}".format(cp_loglist[i  + gap + n - 1].log_timestamp, os.path.basename(pic.path))))
            else:
                logger.info(__(">>>>Association de log {0} avec pic {1}".format(cp_loglist[i  + gap + n - 1].log_timestamp, pic.path)))
            """# On recalcule le delta habituel entre le log et les images
            # TODO peut-être renommer la variable avg_delta, qui n'est plus une moyenne.
            # ou bien affecter avg_delta vers une autre variable
            avg_delta = (loglist[i + gap + n - 1].log_timestamp - pic.DateTimeOriginal).total_seconds()
            print("Average delta : {0}".format(avg_delta))"""
        except Exception as e:
            logger.warning(__("Exception: {}".format(e)))
            #import pdb; pdb.set_trace()
            #print("i, gap, n")
            #print("End of list")
                

        gap = gap + n - 1
        """
        for missing_pic in range(n - 1):
            piclist_corrected.insert(len(piclist_corrected) - 1, None)
            # display information
            try:
                print("=" * 30)
                print("Il manque une photo pour {0} :".format(cp_loglist[i + gap]))
                print(os.path.basename(piclist[i - 1].path))
                print("et")
                print(os.path.basename(piclist[i].path))
                print("-" * 30)
                #print("index de la photo : ", i)
                #print(loglist[i + gap + n - 3])
                #print(loglist[i + gap + n - 2])
                #print(loglist[i + gap + n - 1])
                #print("="*30)
                # add a gap to correlate the next pic with the correct log_timestamp
            except Exception as e:
                #print (e)
                pass
            #gap += 1
            #print("Gap est à : ", gap)
        """    
     
    # piclist_corrected = [i for i in piclist_corrected if (type(i) == New_Picture_infos and type(i.path) != None) or type(i) == bool]
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    # print("standard deviation : ", deviation)
    
    
    """for pic in piclist_corrected:
        if isinstance(pic, New_Picture_infos):
            try:
            #pourquoi ce print ne marche pas en logger.info ??
                print(os.path.basename(pic.path),
                                 pic.New_DateTimeOriginal,
                                 pic.DateTimeOriginal,
                                 (pic.New_DateTimeOriginal - pic.DateTimeOriginal).total_seconds(),
                                 )
            except TypeError:
                logger.info("Virtual Image")
        else:
            logger.info("Pas une image")
    """
    #TODO Attention, ce nouvel appel à manual_timestamp ne permettra pas de faire
    # faire des modifications, puisque qu'il faut refaire la correlation ensuite.
    # trouver une solution élégante pour ça. Soit supprimer la possibilité de faire des
    # modifs, soit refaire la correlation ensuite.
    piclist_corrected=manual_timestamp(camera_obj, loglist, piclist_corrected)
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    print("standard deviation : ", deviation)
    
    return piclist_corrected, deviation

def correlate_nearest_time_manual(camera_obj, loglist = None, piclist = None, user_delta = True):
    """Try to find the right image for each log's timestamp.
    Find the closest image for each timestamp in the log.
    :param user_delta:
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""

    # calcule le delta moyen log-pic sur les premiers 5% des photos
    
    if loglist == None : loglist = camera_obj.log_list
    if piclist == None : piclist = camera_obj.image_list
    idx_start = 0
    idx_range = 200
    total_lenght = len(loglist)
    
    piclist = manual_timestamp(loglist, piclist)
            
    if user_delta:
            user_delta = input("Enter a new delta value: ")
            if user_delta is not None:
                avg_delta = float(user_delta)
        
        

            
    #import pdb; pdb.set_trace()
    piclist_corrected = []
    print("len loglist:{0}".format(len(loglist)))
    print("len piclist:{0}".format(len(piclist)))
    for i, pic in enumerate(piclist):
        n = 1
        #print("i, gap, n", i, gap, n)
        #delta = abs((loglist[i + gap].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
        #print("loglist {0} et piclist {1}".format(i+gap + n, i))
        #if len(piclist_corrected) > 0 and piclist_corrected[-1].new_datetimeoriginal >= log
        try:
            delta = abs((loglist[i].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
            next_delta = abs((loglist[i + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
            if pic.path is not None:
                print("A Calcul de la diff entre {0} et {1}".format(loglist[i].log_timestamp, os.path.basename(pic.path)))
                print("B Calcul de la diff entre {0} et {1}".format(loglist[i + n].log_timestamp, os.path.basename(pic.path)))
                
            while next_delta <= delta:
                print("="*10)
                print("delta  = {0} pour loglist {1} et piclist {2}".format(delta, loglist[i].log_timestamp, os.path.basename(pic.path)))
                print("delta2 = {0} pour loglist {1} et piclist {2}".format(abs((loglist[i + n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta), loglist[i + n].log_timestamp, os.path.basename(pic.path)))
                delta = next_delta
                n = n + 1
                next_delta = abs(
                    (loglist[i +  n].log_timestamp - pic.DateTimeOriginal).total_seconds() - avg_delta)
                    
            new_datetimeoriginal = loglist[i + n - 1].log_timestamp
            new_subsectimeoriginal = "%.6d" % (loglist[i + n - 1].log_timestamp.microsecond)
            piclist_corrected.append(New_Picture_infos(pic.path, pic.DateTimeOriginal, pic.SubSecTimeOriginal,
                                                   new_datetimeoriginal, new_subsectimeoriginal, "", "", "", ""))
                                                   
            if pic.path is not None:
                print(">>>>Association de log {0} avec pic {1}".format(loglist[i  + n - 1].log_timestamp, os.path.basename(pic.path)))
            """# On recalcule le delta habituel entre le log et les images
            # TODO peut-être renommer la variable avg_delta, qui n'est plus une moyenne.
            # ou bien affecter avg_delta vers une autre variable
            avg_delta = (loglist[i + gap + n - 1].log_timestamp - pic.DateTimeOriginal).total_seconds()
            print("Average delta : {0}".format(avg_delta))"""
        except Exception as e:
            print("Exception:", e)
            # print("i, gap, n")
            # print("End of list")
            # pass

        for missing_pic in range(n - 1):
            piclist_corrected.insert(len(piclist_corrected) - 1, None)
            # display information
            try:
                print("=" * 30)
                print("Il manque une photo pour {0} :".format(loglist[i]))
                print(os.path.basename(piclist[i - 1].path))
                print("et")
                print(os.path.basename(piclist[i].path))
                print("-" * 30)
                #print("index de la photo : ", i)
                #print(loglist[i + gap + n - 3])
                #print(loglist[i + gap + n - 2])
                #print(loglist[i + gap + n - 1])
                #print("="*30)
                # add a gap to correlate the next pic with the correct log_timestamp
            except Exception as e:
                #print (e)
                pass
            #gap += 1
            #print("Gap est à : ", gap)
            
        for idx in range(n):
            loglist[i + idx] = loglist[i + idx]._replace(log_timestamp = loglist[i + idx].log_timestamp - datetime.timedelta(days = 20))
        
        
        
        
    # piclist_corrected = [i for i in piclist_corrected if (type(i) == New_Picture_infos and type(i.path) != None) or type(i) == bool]
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    # print("standard deviation : ", deviation)
    #import pdb; pdb.set_trace()
    for pic in piclist_corrected:
        if isinstance(pic, New_Picture_infos):
            try:
                print(os.path.basename(pic.path), pic.New_DateTimeOriginal, pic.DateTimeOriginal, (pic.New_DateTimeOriginal - pic.DateTimeOriginal).total_seconds())
            except Exception as e:
                print(e)
            
    return piclist_corrected, deviation
    
def manual_timestamp(camera_obj, loglist = None, piclist = None, user_delta = True):

    if loglist == None : loglist = camera_obj.log_list
    if piclist == None : piclist = camera_obj.image_list
    idx_start = 0
    idx_range = 100
    total_lenght = len(loglist)
    piclist = piclist[:]
    #import pdb; pdb.set_trace()
    while True:
        delta_list = []
        idx_end = idx_start + idx_range if idx_start + idx_range < total_lenght else total_lenght 
        
        for i, log_line in enumerate(loglist[idx_start:idx_end], idx_start):
            try:
                if piclist[i] is not None and piclist[i].path is not None:
                    delta_list.append((log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds())
                    #TODO ajouter une indication si la cam a répondu (T ou F,  true false) 
                """print("{0:8} : calcul {1}{2} - {3}{4} : {5}".format(i, 
                                                                                        log_line.log_timestamp,
                                                                                        'T' if camera_obj.cam_return[i] == True else 'F',
                                                                                        piclist[i].DateTimeOriginal,
                                                                                        'T' if piclist[i] is not None and piclist[i].path is not None else 'F',
                                                                                        (log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds()))"""
                print("{0:8} : calcul {1}{2} - {3}{4} : {5}".format(i, 
                                                                                        log_line.log_timestamp,
                                                                                        'T' if log_line.cam_return == True else 'F',
                                                                                        piclist[i].DateTimeOriginal,
                                                                                        'T' if piclist[i] is not None and piclist[i].path is not None else 'F',
                                                                                        (log_line.log_timestamp - piclist[i].DateTimeOriginal).total_seconds()))
            except ZeroDivisionError:
                # print("except")
                delta_list.append((loglist[0].log_timestamp - piclist[0].DateTimeOriginal).total_seconds())
            # print(delta_list)
            except IndexError:
                print("{0:8} : calcul {1}{2}".format(i, log_line.log_timestamp, 'T' if log_line.cam_return == True else 'F'))
            except AttributeError:
                print("{0:8} : calcul {1}{2}".format(i, log_line.log_timestamp, 'T' if log_line.cam_return == True else 'F'))
        try:
            avg_delta = sum(delta_list) / len(delta_list)
            print("ecart moyen entre le log et les photos : ", avg_delta)
            print("ecart min : {}".format(min(delta_list)))
            print("ecart max : {}".format(max(delta_list)))
        except ZeroDivisionError as e:
            avg_delta = "ZeroDivisionError"
        #avg_delta = 1.5
        
        
        print("Type 'a10' to insert a virtual pic before index 10")
        print("Type 'r23' to remove a pic at index 23")
        print("Press 'Enter' to go to the next range")
        print("Press 's' to move to the list beginning")
        print("Press 'q' to quit this menu")
        value = input("Your command: ")
        
        if len(value) > 1:
            idx = int(value[1:])
            if value[0].lower() == 'a':
                piclist.insert(idx, New_Picture_infos(None, loglist[idx].log_timestamp, None, None, None, None, None, None, None))
            elif value[0].lower() == 'r':
                del(piclist[idx])
                
            idx_start = idx -5 if idx > 5 else 0
            
        elif len(value) == 0:

            #TODO gérer lorsque index error
            if idx_end + idx_range <= total_lenght:
                idx_start += idx_range
            else:
                idx_start = total_lenght - idx_range
                
        elif len(value) == 1 and value[0].lower() == 'm':
            piclist = insert_missing_timestamp(cam)
            idx_start = 0
            
        elif len(value) == 1 and value[0].lower() == 'q':
            break
                
        elif len(value) == 1 and value[0].lower() == 's':
            idx_start = 0
            
        elif len(value) == 1 and value[0].lower() == 'd':
            import pdb; pdb.set_trace()
            
    print("len loglist:{0}".format(len(loglist)))
    print("len piclist:{0}".format(len(piclist)))
    
    return piclist
    
def correlate_manual(camera_obj, loglist = None, piclist = None, user_delta = True):
    """Try to find the right image for each log's timestamp.
    Find the closest image for each timestamp in the log.
    :param user_delta:
    :param loglist: a list of log_infos nametuple
    :param piclist: a list of Picture_infos namedtuple
    :return: a list of New_Picture_infos namedtuple, the standard deviation between log's timestamp
    and image's timestamp"""
        
    if loglist == None : loglist = camera_obj.log_list
    if piclist == None : piclist = camera_obj.image_list
    piclist = manual_timestamp(cam, loglist, piclist)
    piclist_corrected = []
        
    for log_line, pic in zip(loglist, piclist):
        new_datetimeoriginal = log_line.log_timestamp
        new_subsectimeoriginal = "%.6d" % (log_line.log_timestamp.microsecond)
        # single_cam_image_list[i] = single_cam_image_list[i]._replace(New_DateTimeOriginal=new_datetimeoriginal, New_SubSecTimeOriginal=new_subsectimeoriginal)
        piclist_corrected.append(New_Picture_infos(pic.path,
                                                     pic.DateTimeOriginal,
                                                     pic.SubSecTimeOriginal,
                                                     new_datetimeoriginal, new_subsectimeoriginal, "", "",
                                                     "", ""))
    # piclist_corrected = [i for i in piclist_corrected if (type(i) == New_Picture_infos and type(i.path) != None) or type(i) == bool]
    deviation = standard_deviation(compute_delta3(loglist, piclist_corrected))
    print("standard deviation : ", deviation)
    #import pdb; pdb.set_trace()
    """
    for pic in piclist_corrected:
        if isinstance(pic, New_Picture_infos):
            try:
                print(os.path.basename(pic.path), pic.New_DateTimeOriginal, pic.DateTimeOriginal, (pic.New_DateTimeOriginal - pic.DateTimeOriginal).total_seconds())
            except Exception as e:
                print(e)
    """        
    
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


def insert_missing_timestamp(cam):
    """Insert missing timestamp in the piclists, when the log indicate that the cam didn't answer to the shutter request
    :param cam: a Cam_Infos object
    :return: the list of Picture_infos namedtuple with the missing timestamp inserted
    """
    # On insert les timestamps qu'on sait manquants (caméra qui n'ont pas répondu, donc 0 dans le log).
    # Cela évite de fausser les calculs des différences de temps entre chaque images
    new_piclist = []
    gap = 0

    for i, log_line in enumerate(cam.log_list):
        if log_line.cam_return is True:
            try:
                new_piclist.append(cam.image_list[i - gap])
                # print("Ajout en position {0} de {1}".format(i, piclists[cam][i]))
            except:
                # print("End of list")
                pass

        else:
            try:
                new_piclist.append(Picture_infos._replace(path=None, DateTimeOriginal = log_line.log_timestamp))
                gap += 1
                # print("Ajout en position {0} de {1}".format(i, Picture_infos(None, log_line.log_timestamp, 0)))
            except:
                # print("End of list")
                pass
    return new_piclist

    
def correlate_log_and_pic(camera_obj, auto=True):
    """Correlate the images timestamp with the log timestamps.
    If there are more log's timestamps than pic'count, 3 different algorithms will try to find
    which timestamp has no image related to the it.

    :param camera_obj:
    :param auto:
    :return: a new list of New_Picture_infos namedtuple with the more accurate timestamps.
    """
    piclist_corrected = []
    pic_count_diff = cam.log_count - cam.pic_count
    single_cam_image_list = insert_missing_timestamp(cam)
    original_deviation = standard_deviation(compute_delta3(cam.log_list, single_cam_image_list))
    
    if auto:
        

        if pic_count_diff == 0:
            print("Camera {0} : Exact correlation between logfile and pictures".format(camera_obj.name))
            for i, log_line in enumerate(camera_obj.log_list):
                if log_line.cam_return is True:
                    new_datetimeoriginal = log_line.log_timestamp
                    new_subsectimeoriginal = "%.6d" % (log_line.log_timestamp.microsecond)
                    # single_cam_image_list[i] = single_cam_image_list[i]._replace(New_DateTimeOriginal=new_datetimeoriginal, New_SubSecTimeOriginal=new_subsectimeoriginal)
                    single_cam_image_list[i] = New_Picture_infos(single_cam_image_list[i].path,
                                                                 single_cam_image_list[i].DateTimeOriginal,
                                                                 single_cam_image_list[i].SubSecTimeOriginal,
                                                                 new_datetimeoriginal, new_subsectimeoriginal, "", "",
                                                                 "", "")
            
            #piclist_corrected = correlate_nearest_time_manual(camera_obj.log_list, camera_obj.image_list[:])
            
            #deviation = standard_deviation(compute_delta3(camera_obj.log_list, nearest))
            #print("standard deviation after correction: ", deviation)

            
            #debug :
            for pic in piclist_corrected:
                if isinstance(pic, New_Picture_infos):
                    print(os.path.basename(pic.path), pic.New_DateTimeOriginal, pic.DateTimeOriginal, (pic.New_DateTimeOriginal - pic.DateTimeOriginal).total_seconds())


        elif pic_count_diff > 0:
            print("=" * 80)
            print("{0} : {1} Missing pictures".format(camera_obj.name, pic_count_diff))

            # On utilise plusieurs algorithmes différents pour retrouver les images manquantes
            forward = correlate_double_diff_forward(camera_obj, camera_obj.log_list, single_cam_image_list[:], pic_count_diff, cam)
            backward = correlate_double_diff_backward(camera_obj, camera_obj.log_list, single_cam_image_list[:], pic_count_diff, cam)
            nearest = correlate_nearest_time_exclusive(camera_obj, camera_obj.log_list, single_cam_image_list[:])
            #nearest = correlate_nearest_time_exlusive(camera_obj, loglist[:], image_list[cam][:])
            #nearest = correlate_nearest_time_manual(camera_obj, loglist[:], image_list[cam][:])
            
            print("Time deviation before correction : ", original_deviation)
            print("=" * 80)
            print("1 : double diff forward deviation: ", forward[1])
            print("2 : double diff backward deviation: ", backward[1])
            print("3 : nearest time deviation: ", nearest[1])

            user_input = input("The lowest deviation should be the better choice \n"
                                   "Which algorithm do you want to use ? 1, 2 or 3 ? ")
            while True:
                if int(user_input) == 1:
                    piclist_corrected = forward[0]
                    break
                elif int(user_input) == 2:
                    piclist_corrected = backward[0]
                    break
                elif int(user_input) == 3:
                    piclist_corrected = nearest[0]
                    break
                else:
                    print("Invalid choice")



        elif pic_count_diff < 0:
            
            print("=" * 80)
            print("{0} : {1} extra pictures".format(camera_obj.name, abs(pic_count_diff)))
            #nearest = correlate_nearest_time(loglist, image_list[cam], user_delta = True)
            nearest = correlate_nearest_time_exclusive(camera_obj, camera_obj.log_list, camera_obj.image_list[:], user_delta = True)
            print("Time deviation before correction : ", original_deviation)
            print("=" * 80)
            #print("1 : double diff forward deviation: ", forward[1])
            #print("2 : double diff backward deviation: ", backward[1])
            print("nearest time deviation: ", nearest[1])
            piclist_corrected = nearest[0]

    else:
        single_cam_image_list = insert_missing_timestamp(cam)
        #nearest, deviation = correlate_nearest_time_exlusive(camera_obj.log_list, camera_obj.image_list[:], user_delta = True)
        #piclist_corrected, deviation = correlate_manual(camera_obj, camera_obj.log_list, nearest, user_delta = True)
        #piclist_corrected, deviation = correlate_manual(camera_obj, camera_obj.log_list, camera_obj.image_list[:], user_delta = True)
        piclist_corrected, deviation = correlate_manual(camera_obj, camera_obj.log_list, single_cam_image_list, user_delta = True)
        #piclist_corrected, deviation = correlate_nearest_time_exclusive(camera_obj, camera_obj.log_list, camera_obj.image_list[:], user_delta = True)
        
        #piclist_corrected, deviation = correlate_nearest_time_exclusive(camera_obj, camera_obj.log_list, single_cam_image_list, user_delta = True)
            
    return piclist_corrected


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
            pass
            print("Impossible de calculer le delta")
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


def parse_log(path_to_logfile, camera_count):
    """Parse the log file generated by the raspberry pi, to keep only the shutters timestamps
    and the related informations
    :param path_to_logfile: path to the logfile
    :param camera_count: how many camera were used in the logfile
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
            try:
                loglist.append(log_infos(datetime.datetime.fromtimestamp(float(line[0])), line[1],
                                         datetime.datetime.fromtimestamp(float(line[5])), int(line[3]), bin(int(line[2]))[2:].zfill(camera_count),
                                         int(line[4])))

            except Exception as e:
                print("parse error: ", e)
    logfile.close()
    return loglist


def geotag_from_gpx(piclist, gpx_file, offset_time=0, offset_bearing=0, offset_distance=0):
    """This function will try to find the location (lat lon) for each pictures in each list, compute the direction
    of the pictures with an offset if given, and offset the location with a distance if given. Then, these
    coordinates will be added in the New_Picture_infos namedtuple.
    :param piclist:
    :param gpx_file: a gpx or nmea file path
    :param offset_time: time offset between the gpx/nmea file, and the image's timestamp
    :param offset_bearing: the offset angle to add to the direction of the images (for side camera)
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

    #for piclist, offset_bearing in zip(piclists, offset_bearings):

    start_time = time.time()
    print("===\nStarting geotagging of {0} images using {1}.\n===".format(len(piclist), gpx_file))

    # for filepath, filetime in zip(piclist.path, piclist.New_DateTimeOriginal):
    for i, pic in enumerate(piclist):
        # add_exif_using_timestamp(filepath, filetime, gpx, time_offset, bearing_offset)
        # metadata = ExifEdit(filename)
        #import pdb; pdb.set_trace()
        t = pic.New_DateTimeOriginal - datetime.timedelta(seconds=offset_time)
        #t = t.replace(tzinfo=tzlocal()) # <-- TEST pour cause de datetime aware vs naive
        
        try:
            lat, lon, bearing, elevation = interpolate_lat_lon(gpx, t)
            corrected_bearing = (bearing + offset_bearing) % 360
            # Apply offset to the coordinates if distance_offset exists
            if offset_distance != 0:
                #new_Coords = LatLon(lat, lon).offset(corrected_bearing, offset_distance / 1000)
                #lat = new_Coords.lat.decimal_degree
                #lon = new_Coords.lon.decimal_degree
                lon, lat, unusedbackazimuth = (pyproj.Geod(ellps='WGS84').fwd(lon, lat, corrected_bearing, offset_distance))
            # Add coordinates, elevation and bearing to the New_Picture_infos namedtuple
            piclist[i] = pic._replace(Longitude=lon, Latitude=lat, Ele=elevation, ImgDirection=corrected_bearing)

        except ValueError as e:
            print("Skipping {0}: {1}".format(pic.path, e))
            
        except TypeError as f:
            print("Skipping {0}: {1} - {2}".format(pic.path, f, i))

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
                wgs84_geod = Geod(ellps='WGS84')
                azimuth1, azimuth2, distance = wgs84_geod.inv(next_pic.Longitude, next_pic.Latitude, pic.Longitude, pic.Latitude)
               
                #distance = vincenty((next_pic.Latitude, next_pic.Longitude), (pic.Latitude, pic.Longitude)).meters
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
            try:
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
        print("Success!") if "OK" in answer else print("Error!")
        r.close()
    except Exception as e:
        print("Error! Can't send the session to Josm", e)


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
                                                 " V4MPOD, and geolocalize them")
    parser.add_argument('--version', action='version', version='0.2')
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
    parser.add_argument("-n", "--no_retag", help="Don't ask if you want to restart the images geotagging", action="store_true")
    parser.add_argument("-w", "--write_exif", help="Ask to write the new exif tags in the images", action="store_true")
    parser.add_argument("-x", "--exclude_close_pic", help="Move the too close pictures to the exluded folder", action="store_true")
    parser.add_argument("-c", "--compare", help="Compare Lat/Lon from a cam with another folder, path will be ask during the script", action="store_true")

    args = parser.parse_args()
    print(args)
    return args


def config_parse(profile_name):
    """Parse the profile entered with the command line. This profile is in the profile.cfg file.
    These parameters are used to automate the processing
    :param profile_name: Profile's name"""

    import configparser
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(sys.argv[0]), "profile.cfg"))

    folder_string = config.get(profile_name, "folder_names")
    folder_string = [i.strip() for i in folder_string.split(",")]

    cam_names = config.get(profile_name, "cam_names")
    cam_names = [i.strip() for i in cam_names.split(",")]

    cam_bearing = config.get(profile_name, "cam_bearing")
    cam_bearing = [int(i.strip()) for i in cam_bearing.split(",")]
    
    cam_log_count = int(config.get(profile_name, "cam_log_count"))

    distance_from_center = float(config.get(profile_name, "distance_from_center"))
    
    min_pic_distance = float(config.get(profile_name, "min_pic_distance"))
    
    try:
        cam_log_position = config.get(profile_name, "cam_log_position")
        cam_log_position = [int(i.strip()) for i in cam_log_position.strip(",")]
    except:
        cam_log_position = list(range(len(cam_names)))
    

    return folder_string, cam_names, cam_log_position, cam_bearing, cam_log_count, distance_from_center, min_pic_distance


def find_file(directory, file_extension):
    """Try to find the files with the given extension in a directory
    :param directory: the directory to look in
    :param file_extension: the extension (.jpg, .gpx, ...)
    :return: a list containing the files found in the directory"""
    file_list = []
    for root, sub_folders, files in os.walk(directory):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(file_extension)]
    
    # removing correlate.log from the result list
    # TODO Sortir le choix du ou des fichiers de cette fonction. Cela devrait se faire ailleurs
    # par exemple dans main.
    file_list = [x for x in file_list if "correlate.log" not in x]
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
            idx = [i.lower() for i in dir_list].index(string.lower())
            images_path.append(os.path.abspath(os.path.join(working_dir, dir_list[idx])))
        except ValueError:
            print("I can't find {0}".format(string))
            images_path.append("none")
            #sys.exit()
    return images_path

def compare_latlon(piclist1, piclist2, max_distance = 0):
    distance_list=[]
    for pics in zip(piclist1, piclist2):
        pic1, pic2 = pics
        #try:
        wgs84_geod = Geod(ellps='WGS84')
        azimuth1, azimuth2, distance = wgs84_geod.inv(pic2.Longitude, pic2.Latitude, pic1.Longitude, pic1.Latitude)
        #distance = vincenty((pic1.Latitude, pic1.Longitude), (pic2.Latitude, pic2.Longitude)).meters
        
        if distance > max_distance:
            #print("{0} meters between {1} and {2}".format(distance, os.path.basename(pic1.path), os.path.basename(pic2.path)))
            distance_list.append((distance, pic1, pic2))
                
            
    return distance_list

if __name__ == '__main__':
    # Parsing the command line arguments
    args = arg_parse()

    # Trying to find the logfile in the working directory if none is given in the command line
    if args.logfile is None:
        print("=" * 30)
        args.logfile = find_file(args.source, "log")
        
    if args.logfile is None:
        print("No logfile found... Exiting...")
        sys.exit()


    # Trying to find a nmea file in the working directory if none is given in the command line
    if args.gpxfile is None:
        print("=" * 30)
        args.gpxfile = find_file(args.source, "nmea")
    # Or a gpx file if there is no nmea file
    if args.gpxfile is None:
        args.gpxfile = find_file(args.source, "gpx")

    if args.gpxfile is None:
        print("No gpx/nmea file found... Exiting...")
        sys.exit()

    #Parsing the multicam profile
    folder_string, cam_names, cam_log_position, cam_bearings, cam_log_count, distances_from_center, min_pic_distance = config_parse(args.profile)
    

    # Trying to find the folders containing the pictures
    path_to_pics = find_directory(args.source, folder_string)

    # Searching for all the jpeg images
    """image_list = []
    print("=" * 80)
    print("Searching for jpeg images in ... ")
    for path in path_to_pics:
        print(path)
        image_list.append(list_images(path))"""
    cam_group = Cam_Group()
    for cam in zip(cam_names, path_to_pics, cam_bearings, cam_log_position):
        single_cam = Cam_Infos(cam[0], cam[1], cam[2], distances_from_center, cam[3])
        cam_group.append(single_cam)
   

    # Parsing the logfile
    loglist = parse_log(args.logfile, cam_log_count)
    
    cam_group.add_log(loglist)
    cam_group.get_image_list()
      
    # Trying to correlate the shutter's timestamps with the images timestamps.
    for cam in cam_group:
        cam.new_image_list = correlate_log_and_pic(cam, auto=False)

        # Remove the unuseful value in the lists
        #piclists_corrected = filter_images(piclists_corrected)

        # Geotag the pictures, add the direction, and offset them from the location
        
    cam_group.filter_images(data=True)
    #import pdb; pdb.set_trace()
    print("=" * 80)
    for cam in cam_group:
        geotag_from_gpx(cam.new_image_list, args.gpxfile, args.time_offset, cam.bearing, cam.distance_from_center)
        print("=" * 80)

    
    # Write a josm session file to check the picture's location before writing the new exif data
    if args.josm:
        session_file_path = os.path.abspath(os.path.join(args.source, "session.jos"))
        write_josm_session([i.new_image_list for i in cam_group], session_file_path, [i.name for i in cam_group], args.gpxfile)
        open_session_in_josm(session_file_path)

    if not args.no_retag:
        print("=" * 80)
        input_time_offset = 0
        while True:
            user_geo_input = input("Apply a time offset and restart geotag? (value or n) : ")
            #TODO chercher pourquoi lorsqu'on avait des photos avec une géolocalisation OK, mais que volontairement
            # on applique un offset complètement en dehors de la plage horaire, la nouvelle correlation semble conserver
            # les Lat/Lon précédents.
            if user_geo_input.lower() == "n":
                break
            try:
                input_time_offset = float(user_geo_input)
                print("=" * 80)
                for cam in cam_group:
                    geotag_from_gpx(cam.new_image_list, args.gpxfile, args.time_offset + input_time_offset,
                                cam.bearing, cam.distance_from_center)
                print("=" * 80)
                if args.josm:
                    cam_names = [i.name for i in cam_group]
                    new_cam_names = [name + " | " + str(input_time_offset) for name in cam_names]
                    write_josm_session([i.new_image_list for i in cam_group], session_file_path, new_cam_names)
                    open_session_in_josm(session_file_path)
            except ValueError:
                print("Invalid input")
                
    if args.compare:
        for cam in cam_group:
            max_distance = 1
            user_input = input("Enter the path to compare lat/lon with  {}:\n ".format(cam.name))
            piclist2 = list_geoimages(str(user_input))
            compare_result = compare_latlon(cam.new_image_list, piclist2, max_distance)
            for result in compare_result:
                logger.info(__("{0} meters between {1} and {2}".format(result[0], os.path.basename(result[1].path), os.path.basename(result[2].path))))
            logger.info(__("{} pictures couple have more than {} meters between them".format(len(compare_result), max_distance)))

    # Write the new exif data in the pictures.
    print("=" * 80)

    if args.write_exif:
        user_input = input("Write the new exif data in the pictures? (y or n) : ")
        if user_input == "y":
            #remove pictures without lat/long
            #cam_group.filter_images(latlon = True)
            write_metadata([i.new_image_list for i in cam_group])
    # Move the duplicate pictures to the excluded folder
    if args.exclude_close_pic:
        print("Moving pictures too close to each other")
        move_too_close_pic([i.new_image_list for i in cam_group], min_pic_distance)
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

# NOTES
# 2018/07/08 Ca fait plusieurs fois que je remarque que pour obtenir une bonne corrélation, je suis obligé
# de réduire la valeur de avg_delta par rapport à ce qui a été calculé. PAr exemple, 0.8 au lieu de 0.99