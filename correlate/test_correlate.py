#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
#from collections import namedtuple
from correlate_with_log import *
from data_test import *
#Picture_infos = namedtuple('Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal'])
#New_Picture_infos = namedtuple('New_Picture_infos', ['path', 'DateTimeOriginal', 'SubSecTimeOriginal', "New_DateTimeOriginal", "New_SubSecTimeOriginal"])
#log_infos = namedtuple('log_infos', ['log_timestamp', 'action', 'return_timestamp', 'time_to_answer', 'cam_return', 'pic_number', ])

def test_peillac1_nearest00():
    retour01 = correlate_nearest_time(logtest00, pictest00[0][:])
    assert retour01 == result00_00

def test_peillac_backward00():
    retour01 = correlate_double_diff_backward(logtest00, pictest00[0][:], 2, 0)
    assert retour01 == result00_00


logtest01=(
log_infos(datetime.datetime(2017,8,20,18,11,15,235000), "KTakepic", datetime.datetime(2017,8,20,18,11,15,235000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,22,682000), "KTakepic", datetime.datetime(2017,8,20,18,11,22,682000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,24,900990), "KTakepic", datetime.datetime(2017,8,20,18,11,24,900990), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,26,423547), "KTakepic", datetime.datetime(2017,8,20,18,11,26,423547), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,27,983145), "KTakepic", datetime.datetime(2017,8,20,18,11,27,983145), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,29,555789), "KTakepic", datetime.datetime(2017,8,20,18,11,29,555789), 352, "11", 0 ),
)


pictest01 = [
[
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,24), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,29), 0),
],
[
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,24), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,29), 0),
]
]

result01_01 = ([New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), New_SubSecTimeOriginal='682000', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24, 900990), New_SubSecTimeOriginal='900990', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26, 423547), New_SubSecTimeOriginal='423547', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27, 983145), New_SubSecTimeOriginal='983145', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), New_SubSecTimeOriginal='555789', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.25980956098698527)

def test_exact_nearest01():
    retour01 = correlate_nearest_time(logtest01, pictest01[0][:])
    assert retour01 == result01_01
    
pictest02 = [
[
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,29), 0),
],
[
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,29), 0),
]
]

result01_02 = ([New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), New_SubSecTimeOriginal='682000', Longitude="", Latitude="", Ele="", ImgDirection=""), False, New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26, 423547), New_SubSecTimeOriginal='423547', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27, 983145), New_SubSecTimeOriginal='983145', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), New_SubSecTimeOriginal='555789', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.25176751136030245)

result01_02b = ([New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), New_SubSecTimeOriginal='682000', Longitude="", Latitude="", Ele="", ImgDirection=""), False, False, New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27, 983145), New_SubSecTimeOriginal='983145', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), New_SubSecTimeOriginal='555789', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.26829160928782325)


def test_exact_nearest02():
    '''    Il manque une seule photo    '''
    retour01 = correlate_nearest_time(logtest01, pictest02[0][:])
    assert retour01 == result01_02
    
def test_exact_nearest03():
    '''    Il manque 2 photos d'affilée    '''
    retour01 = correlate_nearest_time(logtest01, pictest02[1][:])
    assert retour01 == result01_02b

def test_forward02():
    retour01 = correlate_double_diff_forward(logtest01, pictest02[0][:], 1, 0)
    assert retour01 == result01_02

# Ce test ne fonctionne pas
# def test_backward02():
    # retour01 = correlate_double_diff_backward(logtest01, pictest02[0][:], 1, 0)
    # assert retour01 == result01_02


pictest03 = [
[
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,29), 0),
],
[
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,24), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,27), 0),

]
]

result01_03b = ([New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""), False, New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24, 900990), New_SubSecTimeOriginal='900990', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26, 423547), New_SubSecTimeOriginal='423547', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27, 983145), New_SubSecTimeOriginal='983145', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.3149072061945392)

def test_exact_nearest04():
    '''    Il manque la dernière photo    '''
    retour01 = correlate_nearest_time(logtest01, pictest03[1])
    assert retour01 == result01_03b



# Le test 02 ne fonctionne pas en reverse.
#ET si on ajoute volontairement une ligne de log et d'image au début, avec le même timestamp ?

logtest02=(
log_infos(datetime.datetime(2017,8,20,18,11,14,000000), "KTakepic", datetime.datetime(2017,8,20,18,11,14,000000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,15,235000), "KTakepic", datetime.datetime(2017,8,20,18,11,15,235000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,22,682000), "KTakepic", datetime.datetime(2017,8,20,18,11,22,682000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,24,900990), "KTakepic", datetime.datetime(2017,8,20,18,11,24,900990), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,26,423547), "KTakepic", datetime.datetime(2017,8,20,18,11,26,423547), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,27,983145), "KTakepic", datetime.datetime(2017,8,20,18,11,27,983145), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,29,555789), "KTakepic", datetime.datetime(2017,8,20,18,11,29,555789), 352, "11", 0 ),
)

pictest05 = [
[
Picture_infos("11H14", datetime.datetime(2017,8,20,18,11,14), 0),
Picture_infos("11H15", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("11H22", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("11H26", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("11H27", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("11H29", datetime.datetime(2017,8,20,18,11,29), 0),
]
]

#OUI, ça fonctionne, mais je ne vois que vaguement pourquoi.


# Le test 02 ne fonctionne pas en reverse.
#ET si on ajoute volontairement une ligne de log et d'image au début, et à la fin, avec le même timestamp ?

logtest03=(
log_infos(datetime.datetime(2017,8,20,18,11,14,000000), "KTakepic", datetime.datetime(2017,8,20,18,11,14,000000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,15,235000), "KTakepic", datetime.datetime(2017,8,20,18,11,15,235000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,22,682000), "KTakepic", datetime.datetime(2017,8,20,18,11,22,682000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,24,900990), "KTakepic", datetime.datetime(2017,8,20,18,11,24,900990), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,26,423547), "KTakepic", datetime.datetime(2017,8,20,18,11,26,423547), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,27,983145), "KTakepic", datetime.datetime(2017,8,20,18,11,27,983145), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,29,555789), "KTakepic", datetime.datetime(2017,8,20,18,11,29,555789), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,30,000000), "KTakepic", datetime.datetime(2017,8,20,18,11,30,000000), 352, "11", 0 ),
)

pictest06 = [
[
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,14), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,22), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,27), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,29), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,30), 0),
]
]



logtest04 = [log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 0, 160597), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 0, 569974), time_to_answer=399, cam_return='1111', pic_number=0),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 2, 187858), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 2, 599110), time_to_answer=393, cam_return='1111', pic_number=1),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 4, 216926), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 4, 612862), time_to_answer=385, cam_return='1111', pic_number=2),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 6, 230686), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 6, 635628), time_to_answer=395, cam_return='1111', pic_number=3),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 8, 253722), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 8, 674278), time_to_answer=398, cam_return='1111', pic_number=4),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 10, 292333), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 10, 712028), time_to_answer=388, cam_return='1111', pic_number=5),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 12, 330052), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 12, 747441), time_to_answer=388, cam_return='1111', pic_number=6),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 14, 365517), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 14, 769913), time_to_answer=393, cam_return='1111', pic_number=7),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 16, 387804), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 16, 498858), time_to_answer=102, cam_return='1111', pic_number=8), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 18, 116711), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 18, 609857), time_to_answer=473, cam_return='1111', pic_number=9), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 20, 227895), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 20, 672435), time_to_answer=432, cam_return='1111', pic_number=10),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 25, 290357), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 25, 691281), time_to_answer=391, cam_return='1111', pic_number=11),
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 30, 309305), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 30, 715570), time_to_answer=394, cam_return='1111', pic_number=12), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 32, 333543), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 32, 747192), time_to_answer=405, cam_return='1111', pic_number=13), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 34, 365209), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 34, 761420), time_to_answer=387, cam_return='1111', pic_number=14), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 36, 380115), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 36, 809984), time_to_answer=397, cam_return='1111', pic_number=15), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 38, 427969), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 38, 845414), time_to_answer=385, cam_return='1111', pic_number=16), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 40, 463410), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 40, 882716), time_to_answer=396, cam_return='1111', pic_number=17), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 42, 500681), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 42, 924294), time_to_answer=395, cam_return='1111', pic_number=18), 
log_infos(log_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 44, 542367), action='KTakepic', return_timestamp=datetime.datetime(2017, 10, 7, 16, 24, 44, 950691), time_to_answer=387, cam_return='1111', pic_number=19)]
 
#Dans cette liste, il manque la photo 16,24,6 et 16,24,40
pictest04 = [
[Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn00s-Cam_avant-YDXJ0050.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn02s-Cam_avant-YDXJ0051.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 2), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn04s-Cam_avant-YDXJ0052.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 4), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn08s-Cam_avant-YDXJ0054.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 8), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn10s-Cam_avant-YDXJ0055.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 10), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn12s-Cam_avant-YDXJ0056.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 12), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn14s-Cam_avant-YDXJ0057.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 14), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn16s-Cam_avant-YDXJ0058.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 16), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn18s-Cam_avant-YDXJ0059.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 18), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn20s-Cam_avant-YDXJ0060.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 20), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn25s-Cam_avant-YDXJ0061.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 25), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn30s-Cam_avant-YDXJ0062.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 30), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn32s-Cam_avant-YDXJ0063.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 32), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn34s-Cam_avant-YDXJ0064.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 34), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn36s-Cam_avant-YDXJ0065.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 36), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn38s-Cam_avant-YDXJ0066.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 38), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn42s-Cam_avant-YDXJ0068.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 42), SubSecTimeOriginal=0),
 Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn44s-Cam_avant-YDXJ0069.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 44), SubSecTimeOriginal=0),
]]

result04_04 = ([New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn00s-Cam_avant-YDXJ0050.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 0, 160597), New_SubSecTimeOriginal='160597', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn02s-Cam_avant-YDXJ0051.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 2), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 2, 187858), New_SubSecTimeOriginal='187858', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn04s-Cam_avant-YDXJ0052.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 4), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 4, 216926), New_SubSecTimeOriginal='216926', Longitude="", Latitude="", Ele="", ImgDirection=""), False, New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn08s-Cam_avant-YDXJ0054.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 8), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 8, 253722), New_SubSecTimeOriginal='253722', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn10s-Cam_avant-YDXJ0055.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 10), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 10, 292333), New_SubSecTimeOriginal='292333', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn12s-Cam_avant-YDXJ0056.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 12), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 12, 330052), New_SubSecTimeOriginal='330052', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn14s-Cam_avant-YDXJ0057.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 14), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 14, 365517), New_SubSecTimeOriginal='365517', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn16s-Cam_avant-YDXJ0058.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 16), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 16, 387804), New_SubSecTimeOriginal='387804', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn18s-Cam_avant-YDXJ0059.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 18), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 18, 116711), New_SubSecTimeOriginal='116711', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn20s-Cam_avant-YDXJ0060.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 20), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 20, 227895), New_SubSecTimeOriginal='227895', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn25s-Cam_avant-YDXJ0061.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 25), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 25, 290357), New_SubSecTimeOriginal='290357', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn30s-Cam_avant-YDXJ0062.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 30), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 30, 309305), New_SubSecTimeOriginal='309305', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn32s-Cam_avant-YDXJ0063.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 32), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 32, 333543), New_SubSecTimeOriginal='333543', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn34s-Cam_avant-YDXJ0064.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 34), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 34, 365209), New_SubSecTimeOriginal='365209', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn36s-Cam_avant-YDXJ0065.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 36), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 36, 380115), New_SubSecTimeOriginal='380115', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn38s-Cam_avant-YDXJ0066.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 38), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 38, 427969), New_SubSecTimeOriginal='427969', Longitude="", Latitude="", Ele="", ImgDirection=""), False, New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn42s-Cam_avant-YDXJ0068.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 42), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 42, 500681), New_SubSecTimeOriginal='500681', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='E:\\Mapillary\\2017-10-07_16H24mn00s\\avant\\2017-10-07_16H24mn44s-Cam_avant-YDXJ0069.jpg', DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 44), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 10, 7, 16, 24, 44, 542367), New_SubSecTimeOriginal='542367', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.10942706843430718)

def test_exact_nearest05():
    '''    Il manque la dernière photo    '''
    retour01 = correlate_nearest_time(logtest04, pictest04[0])
    assert retour01 == result04_04
    
logtest05=(
log_infos(datetime.datetime(2017,8,20,18,11,15,235000), "KTakepic", datetime.datetime(2017,8,20,18,11,15,235000), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,22,682000), "KTakepic", datetime.datetime(2017,8,20,18,11,22,682000), 352, "00", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,24,900990), "KTakepic", datetime.datetime(2017,8,20,18,11,24,900990), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,26,423547), "KTakepic", datetime.datetime(2017,8,20,18,11,26,423547), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,27,983145), "KTakepic", datetime.datetime(2017,8,20,18,11,27,983145), 352, "11", 0 ),
log_infos(datetime.datetime(2017,8,20,18,11,29,555789), "KTakepic", datetime.datetime(2017,8,20,18,11,29,555789), 352, "10", 0 ),
)


pictest05 = [
[
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,24), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("blah", datetime.datetime(2017,8,20,18,11,27), 0),
],
[
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,15), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,24), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,26), 0),
Picture_infos("mouarf", datetime.datetime(2017,8,20,18,11,29), 0),
]
]

result05_05a = [Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0), Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), SubSecTimeOriginal=0), Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0), Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0), Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0), Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), SubSecTimeOriginal=0)]

result05_05b = ([New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), New_SubSecTimeOriginal='682000', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24, 900990), New_SubSecTimeOriginal='900990', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26, 423547), New_SubSecTimeOriginal='423547', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path='blah', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 27, 983145), New_SubSecTimeOriginal='983145', Longitude="", Latitude="", Ele="", ImgDirection=""), New_Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), New_SubSecTimeOriginal='555789', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.39484923426824853)

result05_05c = [Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0), Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), SubSecTimeOriginal=0), Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0), Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0), Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29), SubSecTimeOriginal=0)]

result05_05d = ([
New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 15, 235000), New_SubSecTimeOriginal='235000', Longitude="", Latitude="", Ele="", ImgDirection=""), 
New_Picture_infos(path=None, DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 22, 682000), New_SubSecTimeOriginal='682000', Longitude="", Latitude="", Ele="", ImgDirection=""),
New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 24, 900990), New_SubSecTimeOriginal='900990', Longitude="", Latitude="", Ele="", ImgDirection=""), 
New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 26, 423547), New_SubSecTimeOriginal='423547', Longitude="", Latitude="", Ele="", ImgDirection=""), 
False, 
New_Picture_infos(path='mouarf', DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29), SubSecTimeOriginal=0, New_DateTimeOriginal=datetime.datetime(2017, 8, 20, 18, 11, 29, 555789), New_SubSecTimeOriginal='555789', Longitude="", Latitude="", Ele="", ImgDirection="")], 0.3034404839749633)


def test_missing_timestamp():
    result = insert_missing_timestamp(logtest05, pictest05, 0)
    assert result == result05_05a

def test_2failed_nearest01():
    '''        '''
    retour01 = correlate_nearest_time(logtest05, result05_05a)
    assert retour01 == result05_05b
    
def test_missing_timestamp2():
    result = insert_missing_timestamp(logtest05, pictest05, 1)
    assert result == result05_05c

    
def test_1failed_nearest02():
    '''        '''
    retour01 = correlate_nearest_time(logtest05, result05_05c)
    assert retour01 == result05_05d

def test_2failed_forward01():
    '''        '''

    retour01 = correlate_double_diff_forward(logtest05, result05_05c, 1, 1)
    assert retour01 == result05_05d
