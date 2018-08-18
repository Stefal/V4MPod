#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, pyexiv2, datetime
#from datetime import datetime

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
        metadata = pyexiv2.ImageMetadata(filepath)
        metadata.read()
        try:
            t = metadata["Exif.Photo.DateTimeOriginal"].value
            #print t
            #print type(t)
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
        metadata = pyexiv2.ImageMetadata(image[0])
        metadata.read()
        metadata["Exif.Photo.DateTimeOriginal"] = image[1]
        metadata["Exif.Photo.SubSecTimeOriginal"] = image[2]
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
            
    
        
def main(path):
    images_list=list_images(path)
    print("le chemin est ", path)

    #on créé une nouvelle liste avec des tuples comprenant le chemin des images, leurs datetimeoriginal, et la différence de temps avec la précédente
    newlist = []
    for i,pic in enumerate(images_list):
        newlist.append((images_list[i][0], images_list[i][1], int((images_list[i][1]-images_list[i-1][1]).total_seconds())))
    
    #Calcul du délai moyen
    print("Le delai moyen est :", ((newlist[len(newlist)-1][1]-newlist[0][1]).total_seconds()+1)/len(newlist))

    #print_list(newlist)
    
    #Création du générateur
    for group in generate_group(newlist):
        #import pdb; pdb.set_trace()
        gap_list=[(0,group[0][0],group[0][1])]
        
        print("NOUVEAU GROUPE")
        #print_list(group)
        for i,j in enumerate(group):
            #print i,j
            

            if(j[2]==2 and i > 0):
                gap_list.append((i,j[0],j[1]))
                #print_list(newlist)
                #print("gap de 2 secondes : ", i, j[2])
                #corrected_interval = ((newlist[i][1]-newlist[0][1]).total_seconds())/(len(newlist[:i]))
                #print("l'interval est de : ",newlist[i][1], '-', newlist[0][1], 'divise par ',(len(newlist[:i])))
                #print("l'interval est de : ", ((newlist[i][1]-newlist[0][1]).total_seconds()), 'divise par', (len(newlist[:i])))
                #print("l'interval est de : ", corrected_interval)

        for i, gap in enumerate (gap_list):
            pic_index_start = gap_list[i-1][0]
            pic_index_end = gap_list[i][0]
            pic_timestamp_start = gap_list[i-1][2]
            pic_timestamp_end = gap_list[i][2]
            
            if i == 0:
                None #Nothing to do for the first tuple...yes it's ugly... try for i, gap in enumerate (gap_list[1:]):
            else:
                corrected_interval = (pic_timestamp_end-pic_timestamp_start).total_seconds()/(pic_index_end - pic_index_start)
                print("Interval est de : ", (pic_timestamp_end-pic_timestamp_start).total_seconds(), "divise par ", (pic_index_end - pic_index_start))
                print("Interval est de : ", corrected_interval)
                # La dernière tranche n'est pas encore gérée,(celle après le dernier gap de 2)
                print("je tente d'envoyer interpolate_timestamp (newlist[", pic_index_start, pic_index_end, corrected_interval)
                #print("j'ai commente la reecriture")
                interpolate_timestamp(group[pic_index_start:pic_index_end], corrected_interval)

            
            
            

    #print_list(newlist)
              
    print("End of Script")

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: python intertime.py path")
        raise IOError("Bad input parameters")
    
    #path="e:\\pic"
    #path="E:\\Mapillary\\2016-09-15"
    path = sys.argv[1]
    main(path)
	

