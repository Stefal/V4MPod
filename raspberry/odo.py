import os
import sys
import time
import datetime
import subprocess
import threading
import queue

 
#Hall sensor pin
hall_pin=25

#Hall pulse queue
hall_pulse_queue = queue.Queue()

#Wheel radius (meter)
wradius = 0.35
circumference = 2*3.1415*wradius


def hallc(hall_pin=15):
    hall_pulse_queue.put(time.time())
    #print('Edge detected on pin %s' %hall_pin)

  


class shutter_ctrl(threading.Thread):
    """To send shutter to the cameras"""
    def __init__(self, queue, speed_obj, distance_interval = 0, time_interval = 0, mode = "distance", rate = 0.01):
        """
        param: queue: A queue.Queue object
        param: time_interval: the time interval between each picture in time-base mode
        param: distance_obj: a speedometer class instance
        param: mode: "distance" or "time" base mode
        param: rate: refresh rate
        """ 
        threading.Thread.__init__(self)
        self.queue = queue
        self.distance_interval = distance_interval
        self.time_interval = time_interval
        self.min_time = 1
        self.speed_obj = speed_obj
        self.mode = mode if mode == "time" else "distance"
        self.rate = rate
        self.prev_distance = 0
        self.prev_time = time.time()
        self.shutter_count = 0
        self._pause = False
        self._stop = False
        
    def run(self):
        while not self._stop:
            while not self._pause:
                if self.mode == "time":
                    self.time_base()
                elif self.mode == "distance":
                    self.distance_base()
                time.sleep(self.rate)
            time.sleep(self.rate)
        
    def time_base(self):
        
        if self.prev_time + self.time_interval <= time.time():
            print("shutter: {0}".format(self.shutter_count))
            self.shutter_count +=1
            self.prev_time = time.time()
            #TODO tenir compte d'un temps minimum entre chaque déclenchement
            #TODO reprendre le code qui vérifie que le déclenchement a eu lieu       
            
    def distance_base(self):
        try:
            time_interval = self.distance_interval / self.speed_obj.speed
            
        except ZeroDivisionError:
            # when speed is 0, add a very long time
            time_interval = time.time() + 3600 
        
        self.time_interval = time_interval
        #control de l'augmentation de la distance.
        if self.speed_obj.total_distance > self.prev_distance:
            self.time_base()
            self.prev_distance = self.speed_obj.total_distance
            
        #TODO regarder pourquoi le premier déclenchement après un arrêt
        # du vélo (speed = 0), arrive un peu trop vite.
            
    def stop(self):
        self._stop = True
            
    def pause(self):
        self._pause = True
        
    def resume(self):
        self._pause = False
        


class speedometer(threading.Thread):
    """Speed and distance class, which run in a separate thread
    This class read the pulses from a sensor on a wheel, to compute speed and
    distance.
    Each pulse should be a timestamp and is in a queue.
    """
    def __init__(self, wheel_radius, magnet, queue, rate=0.01):
        """init the class with these parameters
        :param wheel_radius: the wheel radius, in meters
        :param magnet: how many magnets are on the wheel
        :param queue: The queue the class should get pulses timestamps from
        :param rate: Refresh speed rate (default to 10 milliseconds)
        """
        threading.Thread.__init__(self)
        self.pulse_distance = wheel_radius*2*3.1415 / magnet
        self.queue = queue
        self.prev_time = time.time()
        self.total_distance = 0
        self.speed = 0
        self.rate = rate
        self._stop = False
    
    def run(self):
        while not self._stop:
            self.read_queue()
            time.sleep(self.rate)
        
    def read_queue(self):
                    
        for pulse_count in range(self.queue.qsize() + 1):
            try:
                pulse_timestamp = self.queue.get(timeout = 2)
                elapsed_time = pulse_timestamp - self.prev_time
                self.speed = self.pulse_distance / elapsed_time
                self.total_distance += self.pulse_distance
                self.prev_time = pulse_timestamp
                
            except queue.Empty:
                self.speed = 0
            
            finally:
                pass
                #print("Distance : {0} - Vitesse : {1}m/s".format(self.total_distance, self.speed))
 
    def stop(self):
        self._stop = True


def loop_test(lenght = 30, speed = 15):
    for i in range(lenght):
        hallc()
        print("hall tick")
        time.sleep(1/speed)

        
mybike = speedometer(0.25,2,hall_pulse_queue)
mybike.start()
shutterq = queue.Queue()
cam = shutter_ctrl(shutterq, mybike, distance_interval = 5)
cam.start()

loop_test()
