#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for simultaneously copying the pictures from up to 6 cameras.
The primary goal is to copy the pictures from 4 action-cams, make groups of pictures with a cutoff time, create
a subfolder for each cam and copy the renamed pictures (timestamp added to the filename).
Let's say you have two cams, with sd cards named "front" and "back".

front sdcard :
ROOT/DCIM/YDXJ0025.jpg (timestamp is 2017-02-01_11h21mn10s)
ROOT/DCIM/YDXJ0026.jpg (timestamp is 2017-02-01_11h21mn11s)
ROOT/DCIM/YDXJ0027.jpg (timestamp is 2017-02-01_11h21mn12s)
ROOT/DCIM/YDXJ0028.jpg (timestamp is 2017-02-01_11h26mn42s)
ROOT/DCIM/YDXJ0029.jpg (timestamp is 2017-02-01_11h26mn43s)

back sdcard :
ROOT/DCIM/YDXJ0112.jpg (timestamp is 2017-02-01_11h21mn10s)
ROOT/DCIM/YDXJ0113.jpg (timestamp is 2017-02-01_11h21mn11s)
ROOT/DCIM/YDXJ0114.jpg (timestamp is 2017-02-01_11h21mn12s)
ROOT/DCIM/YDXJ0115.jpg (timestamp is 2017-02-01_11h26mn42s)
ROOT/DCIM/YDXJ0116.jpg (timestamp is 2017-02-01_11h26mn43s)

with the command:
python copy_pic ~/test -s front,back  -c 60

In your test folder you will get:
2017-02-01_11h21mn10s|
			 |front|
				   |2017-02-01_11h21mn10s-Cam_front-YDXJ0025.jpg
			   |2017-02-01_11h21mn11s-Cam_front-YDXJ0026.jpg
			   |2017-02-01_11h21mn12s-Cam_front-YDXJ0027.jpg
			 |back |
			   |2017-02-01_11h21mn10s-Cam_back-YDXJ0112.jpg
			   |2017-02-01_11h21mn11s-Cam_back-YDXJ0113.jpg
			   |2017-02-01_11h21mn12s-Cam_back-YDXJ0114.jpg
2017-02-01_11h26mn42s|
			 |front|
				   |2017-02-01_11h26mn42s-Cam_front-YDXJ0028.jpg
			   |2017-02-01_11h26mn43s-Cam_front-YDXJ0029.jpg
			 |back |
				   |2017-02-01_11h26mn42s-Cam_back-YDXJ0115.jpg
			   |2017-02-01_11h26mn43s-Cam_back-YDXJ0116.jpg


#source : http://stackoverflow.com/questions/12672981/python-os-independent-list-of-available-storage-devices
"""
""" TODO :
- Calculate the total size to copy, and the space left on the destination
"""
import os, subprocess, sys, datetime, shutil, time, argparse
from lib.exif_read import ExifRead as EXIF
from threading import Thread
from queue import Queue
from concurrent.futures import ThreadPoolExecutor


def arg_parse():
    """ Parse the command line you use to launch the script """
    
    parser= argparse.ArgumentParser(description="A tool to copy pictures from multiple external sources")
    parser.add_argument("destination", nargs="?", help="Path destination for the pictures. Without this parameter, "
                                                       "the script will use the current directory as the destination", default=os.getcwd())
    parser.add_argument("--version", action="version", version="%(prog)s 0.02")
    parser.add_argument("-s", "--source", help="Name of the volume's sources", default="avant, droite, arriere, gauche, pla_droite, pla_gauche")
    parser.add_argument("-c", "--cut", help="Min time between two pictures to create a new group (in seconds)",
                        default=10, type=int)
    parser.add_argument("-a", "--allgroups", help="Copy all groups of pictures without asking.", action="store_true")
    args = parser.parse_args()
    print(args)
    return args


def list_jpg(directory, camid=None):
    """ Search for all the jpg found in a folder and all the subfolders

	Return a list of list containing the camid, the complete path of the
	picture (string), and its DatetimeOriginal (datetime object from the Exif header)
	[['camid', '/mypath/mydirectory/mypicture.jpg', 'datetime.datetime']]
	"""

    file_list = []
    for root, subfolders, files in os.walk(directory):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]
    files = []
    # get DateTimeOriginal data from the images and sort the list by timestamp
    for filepath in file_list:
        metadata = EXIF(filepath)
        
        try:
            t = metadata.extract_capture_time()
            #s = int(t.microsecond / 1000000)
            # print t
            # print type(t)
            # s = metadata["Exif.Photo.SubSecTimeOriginal"].value
            files.append([camid, filepath, t])
        except KeyError as e:
            # if any of the required tags are not set the image is not added to the list
            print("Skipping {0}: {1}".format(filename, e))

    # files.sort(key=lambda timestamp: timestamp[1])
    # print_list(files)
    return files


# return file_list

def get_drive_path(volumename, alldrivelist, drive_type=None):
    """Return the drive letter (windows) or mount point (linux) of a volume's name

	volumename is the name of the volume you want the mount point.

	alldrivelist is a list of drives or volume:
	- Windows: The list should be a list of list, like [['M6500', 3, 'C:', 'OS', 'BEACZ44B'], ['M6500', 3, 'G:', 'FRONT', '964D8E43']]
	with 'M6500', the hostname (string), 3, the drive type (int), 'C:' the drive letter (string),
	'OS' the drive name (string), and 'BEACZ44B' as the drive serial number (string)
	
	- Gnu/Linux: The list should be the /proc/mounts files content, filtered (only dev/sdx lines)

	drive_type could be use to include only some type of drive e.g. only the removable drive (Windows only)
	"""
    if drive_type != None:
        alldrivelist = [drive for drive in alldrivelist if drive[drive_type_index] == drive_type]
    if 'win32' in sys.platform:
        for drive in alldrivelist:
            if drive[3].lower() == volumename.lower():
                return drive[2]
    elif 'linux' in sys.platform:
        for drive in alldrivelist:
            for elt in drive.split():
                if volumename.lower() in elt.lower():
                    return elt
    elif 'darwin' in sys.platform:
        for drive in alldrivelist:
            if drive.lower() == volumename.lower():
                return "/Volumes/" + drive


def get_drivelist():
    """Return a list of drives connected to the computer
	- Windows:  return host, name,volumename, drivetype, volumeserialnumber
	- Gnu/Linux: /proc/mounts files content, filtered (only dev/sdx lines)
	"""
    if 'win32' in sys.platform:

        wmic_out = subprocess.Popen('wmic logicaldisk get name,volumename, drivetype, volumeserialnumber /Format:"%WINDIR%\System32\wbem\en-us\csv"',
                                     shell=True, stdout=subprocess.PIPE)
        drivelistout, err = wmic_out.communicate()
        drivelist = drivelistout.decode(errors="ignore").replace("\r", "").split("\n")
        drivelist = [drive.split(",") for drive in drivelist if drive != ""]
        drive_type_index = drivelist[0].index("DriveType")
        drive_letter_index = drivelist[0].index("Name")
        volume_name_index = drivelist[0].index("VolumeName")
        del drivelist[0]  # Delete columns name
        for drive in drivelist:  # convert drive type to integer
            drive[drive_type_index] = int(drive[drive_type_index])
            # drivefiltered = [drive for drive in drivelist if drive[drive_type_index] == str(2)] #We keep only the drives with type 2


            # driveLines = drivelisto.replace("\r", "").split('\n')

    elif 'linux' in sys.platform:
        with open("/proc/mounts") as f:
            mounts = f.read()
        drivelist = [mount for mount in mounts.split("\n") if "/dev/" in mount[:5]]


    # guess how it should be on mac os, similar to linux , the mount command should
    # work, but I can't verify it...
    elif 'darwin':
        drivelist = os.listdir("/Volumes")

    return drivelist


def find_in_sublist(piclist, groups_start):
    """ find something in the sublists and return the index in the mainlist
	"""
    for i, pic in enumerate(piclist):
        try:
            j = pic.index(groups_start)
        except ValueError as e:
            
            continue
        return i


def listgroup():
    groups.reverse()
    group_start = 0
    while groups:
        group_end = groups.pop()
        print("start : ", group_start, "end : ", group_end)
        for i in range(group_start, group_end):
            print("i = ", i, "pic = ", piclist[i][1])
        print("fin de groupe")
        group_start = group_end
    # print last group
    for i in range(group_start, len(piclist)):
        print("i = ", i, "pic = ", piclist[i][1])
        print("fin de groupe")


def make_pics_groups(piclist, groups):
    """This compare the piclist and the group to generate the group path, and
	send the picture to the "dispatch_to_queue function" """
    groups.reverse()
    cut = groups.pop()
    for i, pic in enumerate(piclist):
        if i == cut:
            group_path = piclist[i][2].strftime("%Y-%m-%d_%HH%Mmn%Ss")
            try:
                cut = groups.pop()
            except:
                pass
        # print group_path, piclist[i][1]
        # rename_and_copy_pic(piclist[i], group_path)
        try:
            dispatch_to_queue(piclist[i], group_path)
        except:
            pass


def dispatch_to_queue(pic, group_path):
    """Send a picture to be copied and his path destination, to a specific queue.
	One queue for each camera/sdcard
	"""

    if volume_names[0] in pic:
        picQueue0.put([pic, group_path])
    elif volume_names[1] in pic:
        picQueue1.put([pic, group_path])
    elif volume_names[2] in pic:
        picQueue2.put([pic, group_path])
    elif volume_names[3] in pic:
        picQueue3.put([pic, group_path])
    elif volume_names[4] in pic:
        picQueue4.put([pic, group_path])
    elif volume_names[5] in pic:
        picQueue5.put([pic, group_path])


def start_copy_thread():
    """Create a thread for each queue, and send it to the "rename_and_copy_pic" function
	"""
    start_time = datetime.datetime.now()
    worker0 = Thread(target=rename_and_copy_pic, args=(picQueue0,))
    worker0.start()
    worker1 = Thread(target=rename_and_copy_pic, args=(picQueue1,))
    worker1.start()
    worker2 = Thread(target=rename_and_copy_pic, args=(picQueue2,))
    worker2.start()
    worker3 = Thread(target=rename_and_copy_pic, args=(picQueue3,))
    worker3.start()
    worker4 = Thread(target=rename_and_copy_pic, args=(picQueue4,))
    worker4.start()
    worker5 = Thread(target=rename_and_copy_pic, args=(picQueue5,))
    worker5.start()
    picQueue0.join()
    picQueue1.join()
    picQueue2.join()
    picQueue3.join()
    picQueue4.join()
    picQueue5.join()
    print(len(piclist[:pic_end]), "pictures copied in", (
        datetime.datetime.now() - start_time).total_seconds(), "seconds")


def rename_and_copy_pic(queue):
    """Take each picture in the queue, and copy it to the destination, with a new name.
	"""
    while not queue.empty():
        picture, group_path = queue.get()
        camid, picture_path, timestamp = picture
        dest_path = os.path.join(dest_folder, group_path, camid)
        if not os.path.exists(dest_path):
            try:
                os.makedirs(dest_path)
            except:
                pass
        picture_name = timestamp.strftime("%Y-%m-%d_%HH%Mmn%Ss") + "-Cam_" + camid + "-" + os.path.basename(
            picture_path)
        print("copying", picture_path, " to ", os.path.join(dest_path, picture_name))
        shutil.copyfile(picture_path, os.path.join(dest_path,
                                                   picture_name))  # TODO: add an option to choose overwrite destination, or skip
        queue.task_done()


def check_user_choice(user_input):
    """Check if the values entered by the user are valid"""

    if len(user_input) > 2:
        return False

    for input in user_input:
        try:
            int(input)
        except ValueError:
            return False

    if int(max(user_input)) > len(groups) or int(min(user_input)) < 0:
        return False

    if int(user_input[0]) > int(user_input[1]):
        return False

    return True


if __name__ == '__main__':

    args = arg_parse()
    dest_folder = args.destination
    cutoff = args.cut
    allgroups = args.allgroups
    volume_names = [volume.strip() for volume in args.source.lower().split(",")]
    print("Searching for volumes....")
    alldrivelist = get_drivelist()
    drivelist = []
    for volume in volume_names:
        drive_letter = get_drive_path(volume, alldrivelist)
        if drive_letter:
            drivelist.append([drive_letter, volume])

    for drive in drivelist:
        print("Volume found: {}   ({})".format(drive[0], drive[1]))
    if len(drivelist) == 0:
        sys.exit("No Volume found !")
    if len(drivelist) > 6:
        sys.exit("Sorry, this script can't manage more than 6 sources \
				If you need more, add some queues and thread, or \
				rewrite the multithread part of this script to dynamicaly handle the number of sources")

    # Check if destination is a source too (bad idea)
    check_dest = find_in_sublist([[drive.lower() for drive in drivedetail] for drivedetail in drivelist],
                       os.path.splitdrive(dest_folder)[0].lower())
    if  type(check_dest) == int:
        sys.exit("Destination is the same as one source.... Exiting")

    piclist = []
    print("Searching for pictures...")
    
   # with ThreadPoolExecutor(max_workers = workers_cnt) as executor:
   #     future_lst = []
   #     for cam in MyCams.cams_list:
   #         future_itm = executor.submit(web_cam_info, cam)
   #         future_lst.append(future_itm)
   #     for future in future_lst:
   #         result = future.result()
   #         cams_status.append(result)
    
    workers_cnt = len(drivelist)
    with ThreadPoolExecutor(max_workers = workers_cnt) as executor:
        future_lst = []
        for drive in drivelist:
            drivepath, volume = drive
            future_itm = executor.submit(list_jpg, drivepath + "/DCIM/", volume)
            future_lst.append(future_itm)
        for future in future_lst:
            result = future.result()
            piclist.extend(result)

    piclist.sort(key=lambda timestamp: timestamp[2])
    groups = []
    groups.append(piclist[0][1])
    ziplist = zip(piclist, piclist[1:])
    # print 'cutoff vaut', cutoff
    print("Computing groups...")

    for pic_couple in ziplist:
        id1, path1, t1 = pic_couple[0]
        id2, path2, t2 = pic_couple[1]
        gap = (t2 - t1)
        # print gap.total_seconds()
        if gap.total_seconds() >= cutoff:
            groups.append(path2)

    for i, group in enumerate(groups):
        groups[i] = find_in_sublist(piclist, group)
        print("Group {0} start : {1}".format(i + 1, piclist[groups[i]][2].strftime("%Y-%m-%d_%HH%Mmn%Ss")))

    input_validity = False
    while input_validity == False:
        if not allgroups:
            user_input = input(
                "\nEnter the group' number you want to copy\nOr enter the group range (e.g. 2-4 to copy the groups 2,3 and 4),\nOr press enter to copy all groups : ").split(
                "-")
        else:
            user_input = ['']

        if user_input == ['']:
            user_input[0] = 1
            user_input.append(len(groups))
        if len(user_input) == 1:
            user_input.append(user_input[0])
        input_validity = check_user_choice(user_input)

    if len(groups) == int(user_input[1]):
        pic_end = len(piclist)
    else:
        pic_end = groups[int(user_input[1])]

    groups_start = int(user_input[0]) - 1
    groups_end = int(user_input[1])

    picQueue0 = Queue()
    picQueue1 = Queue()
    picQueue2 = Queue()
    picQueue3 = Queue()
    picQueue4 = Queue()
    picQueue5 = Queue()

    make_pics_groups(piclist[:pic_end], groups[groups_start:groups_end])
    start_copy_thread()
