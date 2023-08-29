 #!/usr/bin/python

import os, sys

from lib.exif_read import ExifRead as EXIF
from lib.exif_write import ExifEdit
from LatLon3.lat_lon import LatLon,string2latlon,Latitude,Longitude


'''

An offset angele relative to the direction of movement may be given as an optional 
argument to compensate for a sidelooking camera. This angle should be positive for 
clockwise offset. eg. 90 for a rightlooking camera and 270 (or -90) for a left looking camera 

@attention: Requires pyexiv2; see install instructions at http://tilloy.net/dev/pyexiv2/
@author: mprins
@license: MIT
'''
def DMStoDD(degrees, minutes, seconds, hemisphere):
    ''' Convert from degrees, minutes, seconds to decimal degrees. '''
    dms = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if hemisphere == "W" or hemisphere == "S":
        dms = -1 * dms

    return dms

def compute_bearing(start_lat, start_lon, end_lat, end_lon):
    '''
    Get the compass bearing from start to end.

    Formula from
    http://www.movable-type.co.uk/scripts/latlong.html
    '''
    # make sure everything is in radians
    start_lat = math.radians(start_lat)
    start_lon = math.radians(start_lon)
    end_lat = math.radians(end_lat)
    end_lon = math.radians(end_lon)

    dLong = end_lon - start_lon

    dPhi = math.log(math.tan(end_lat/2.0+math.pi/4.0)/math.tan(start_lat/2.0+math.pi/4.0))
    if abs(dLong) > math.pi:
        if dLong > 0.0:
            dLong = -(2.0 * math.pi - dLong)
        else:
            dLong = (2.0 * math.pi + dLong)

    y = math.sin(dLong)*math.cos(end_lat)
    x = math.cos(start_lat)*math.sin(end_lat) - math.sin(start_lat)*math.cos(end_lat)*math.cos(dLong)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

    return bearing


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
    # get GPS data from the images and sort the list by timestamp
    for filepath in file_list:
        metadata = EXIF(filepath)
        try:
            t = metadata.extract_capture_time()
            #lat = metadata["Exif.GPSInfo.GPSLatitude"].value
            #latRef = metadata["Exif.GPSInfo.GPSLatitudeRef"].value
            #lon = metadata["Exif.GPSInfo.GPSLongitude"].value
            #lonRef = metadata["Exif.GPSInfo.GPSLongitudeRef"].value
            geo = metadata.extract_geo()
            direction = metadata.extract_direction()
            files.append((filepath, geo["latitude"], geo["longitude"],  direction))
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filepath, e))

    files.sort()
    return files

def write_exif(filename, coordinates):
    '''
    Write Lat Lon Direction
    '''

    metadata = metadata = ExifEdit(filename)
    #metadata.read()
    
    try:
                
        # convert decimal coordinates into degrees, minutes and seconds as fractions for EXIF
        #exiv_lat = (make_fraction(48,1), make_fraction(58,1), make_fraction(int(52.69876547*1000000),1000000))
        #exiv_lat = (make_fraction(int(coordinates[0]),1), make_fraction(int(coordinates[1]),1), make_fraction(int(float(coordinates[2])*1000000),1000000))
        #exiv_lon = (make_fraction(int(coordinates[4]),1), make_fraction(int(coordinates[5]),1), make_fraction(int(float(coordinates[6])*1000000),1000000))

        # convert direction into fraction
        #exiv_bearing = make_fraction(int(coordinates[8]*10),10)

        # add to exif
        #metadata["Exif.GPSInfo.GPSLatitude"] = exiv_lat
        #metadata["Exif.GPSInfo.GPSLatitudeRef"] = coordinates[3]
        #metadata["Exif.GPSInfo.GPSLongitude"] = exiv_lon
        #metadata["Exif.GPSInfo.GPSLongitudeRef"] = coordinates[7]
        #metadata["Exif.GPSInfo.GPSMapDatum"] = "WGS-84"
        #metadata["Exif.GPSInfo.GPSVersionID"] = '2 0 0 0'
        #metadata["Exif.GPSInfo.GPSImgDirection"] = exiv_bearing
        #metadata["Exif.GPSInfo.GPSImgDirectionRef"] = "T"
        
        metadata.add_lat_lon(coordinates.lat.decimal_degree, coordinates.lon.decimal_degree)
        
        metadata.write()
        print("Added geodata to: {0}".format(filename))
    except ValueError as e:
        print("Skipping {0}: {1}".format(filename, e))


if __name__ == '__main__':
    if len(sys.argv) > 3:
        print("Usage: python move_picture.py path offset (in meters)")
        raise IOError("Bad input parameters.")
    path = sys.argv[1]
    
    
    if len(sys.argv) == 3 :
        offset = float(sys.argv[2])
        print("Offset value is {0} meter(s)".format(offset))

    # list of file tuples sorted by timestamp
    imageList = list_images(path)
    skipped_img = []
    for Img in imageList :
        
        if Img[1] != None and Img[2] != None and Img[3] != None:
            original_coord = LatLon(Latitude(Img[1]), Longitude(Img[2]))
            #print("origine : ", original_coord)
            #print("heading : ", Img[3])
            new_coord = original_coord.offset(Img[3], (offset/1000))
            tuple_coord=new_coord.to_string('d%,%m%,%S%,%H')
            list_coord = ",".join(tuple_coord)
            list_coord = list_coord.split(",")
            list_coord.append(Img[3])
            #import pdb; pdb.set_trace()
            write_exif(Img[0],new_coord)
        else:
            print("Skipping ", Img[0])
            skipped_img.append(Img[0])
    if len(skipped_img) > 0:
        print("Skipped images : ")
        for img in skipped_img:
            print(img)

    print("End of Script")