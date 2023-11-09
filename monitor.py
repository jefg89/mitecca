import threading
import sys
import os
import time
from timeit import default_timer as timer
import subprocess
import random
from datetime import datetime
from random import randrange

import argparse

UTILS_DIR="./utils"


def getAverage(array):
    sum = 0
    for i in range(len(array)):
        sum += array[i]
    return sum / len(array)

class Monitor:
    def __init__(self, mode, refresh_rate):
        self.__refresh = refresh_rate
        self.__inst_file = "mon.out"
        #self.__power_file = "/sys/bus/i2c/drivers/ina3221x/0-0041/iio\:device1/in_power1_input"
        self.__power_file = "power.out"
        self.__perf_thread = threading.Thread(target=self.__pollSThread,args=(UTILS_DIR +"/getinstr.sh " 
                                            + str(self.__refresh) + " " + self.__inst_file, 0))
        self.__power_thread = threading.Thread(target=self.__pollPThread,args=("sudo " + UTILS_DIR +"/getpow.sh " 
                                            + str(self.__refresh) + " " + self.__inst_file, 0))
        self.__exit = False
        self.__core_info = [0,0,0,0,0,0,0]
        self.__power_list = [0,0,0,0,0,0,0,0,0,0]
        self.__power = 200
        self.__mode= mode
        self.__condition = threading.Condition()
        self.__finished = False
    
    def start(self):
        self.__perf_thread.start()
        self.__power_thread.start()
    
    def stop(self):
        self.__exit = True
        #dirty
        with self.__condition:
            self.__condition.notify()
        self.__perf_thread.join()
        self.__power_thread.join()

    def record(self):
        with self.__condition:
            self.__condition.notify()
    
    def isdone(self):
        return self.__finished

    def __pollSThread(self, app_str, core):
        
        str_cmd = "taskset -c " + str(core) + " " + app_str
        command = str_cmd.split(" ")
        while not self.__exit:
                if (self.__mode== "trigger"): 
                    self.__condition.acquire()
                    #print("Waiting for trigger")
                    self.__condition.wait()
                    #print("Triggered received, measuring")
                    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                    p.wait()
                    self.__updateStats()
                    self.__condition.release()
                    #update finished flag
                    self.__finished = True
                else:
                    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                    p.wait()
                    self.__updateStats()



     
    def __pollPThread(self, app_str, core):
        str_cmd = "taskset -c " + str(core) + " " + app_str
        command = str_cmd.split(" ")

        while not self.__exit:
                p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                p.wait()
                time.sleep(0.1)
                self.__updatePower()   
    
    def __updateStats(self):
        while (os.stat(self.__inst_file).st_size == 0):
            time.sleep(0.01)
        for c in range (6):
            self.__core_info[c] = self.__findStatsByCore(c)

    def __updatePower(self):
        curr_power = self.__findPower()
        tmp_list = self.__power_list[1:]
        tmp_list.append(curr_power)
        self.__power_list = tmp_list
        self.__power = getAverage(self.__power_list)

    
    def __findStatsByCore(self, core):
        f = open(self.__inst_file, 'r')
        data = f.readlines()
        f.close()
        res = []
        for d in data:
            if "CPU"+str(core) in d:
                res.append(d)
        return res
    
    def __findPower(self):
        f = open(self.__power_file, 'r')
        pow = int(f.readline())
        f.close()
        return pow

    def getInstructions(self, core):
        instruc = int(self.__core_info[core][0][10:27].replace(".", ''))
        #for l in self.__core_info[core]:
        #    print(l)
        #reset finished flag
        self.__finished = False
        return instruc
    
    def getCacheAccesses(self, core):
        refs = int(self.__core_info[core][2][10:27].replace(".", ''))
        #for l in self.__core_info[core]:
        #    print(l)
        #reset finished flag
        self.__finished = False
        return refs
    
    def getCacheMisses(self,core):
        misses = int(self.__core_info[core][1][10:27].replace(".", ''))
        #for l in self.__core_info[core]:
        #    print(l)
        #reset finished flag
        self.__finished = False
        return misses

    def getPower(self):
        return self.__power
    
    def getEfficiency(self):
        total_instr = 0
        for c in range(6):
            total_instr += self.getInstructions(c)
        return total_instr / (self.__refresh * 0.001 * self.__power)
        

# mon = Monitor("trigger", 1)
# mon.start()
# time.sleep(4)
# while True:
#     mon.record()
#     while not mon.isdone():
#         time.sleep(0.001)
#     for c in range(6):
#         print(mon.getInstructions(c))
#     print("Power = "+ str(mon.getPower()) + "mW")
#     print("***************")

# mon = Monitor("auto", 0.5)
# mon.start()
# time.sleep(4)
# while True:
#     for c in range(6):
#         print(mon.getInstructions(c))
#     print("Power = "+ str(mon.getPower()) + "mW")
#     print("***************")
#     time.sleep(0.5)