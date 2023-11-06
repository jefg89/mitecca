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
    def __init__(self, refresh_rate):
        self.refresh = refresh_rate
        self.inst_file = "mon.out"
        #self.power_file = "/sys/bus/i2c/drivers/ina3221x/0-0041/iio\:device1/in_power1_input"
        self.power_file = "power.out"
        self.perf_thread = threading.Thread(target=self.__pollSThread,args=(UTILS_DIR +"/getinstr.sh " 
                                            + str(self.refresh) + " " + self.inst_file, 0))
        self.power_thread = threading.Thread(target=self.__pollPThread,args=("sudo " + UTILS_DIR +"/getpow.sh " 
                                            + str(self.refresh) + " " + self.inst_file, 0))
        self.finished = False
        self.core_info = [0,0,0,0,0,0,0]
        self.power_list = [0,0,0,0,0,0,0,0,0,0]
        self.power = 200
    
    def start(self):
        self.perf_thread.start()
        self.power_thread.start()
    
    def stop(self):
        self.finished = True
        self.perf_thread.join()
        self.power_thread.join()

    def __pollSThread(self, app_str, core):
        str_cmd = "taskset -c " + str(core) + " " + app_str
        command = str_cmd.split(" ")
        while not self.finished:
                #print(str_cmd)
                p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                #p.wait()
                time.sleep(self.refresh)
                self.__updateStats()
     
    def __pollPThread(self, app_str, core):
        str_cmd = "taskset -c " + str(core) + " " + app_str
        command = str_cmd.split(" ")
        while not self.finished:
                p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                p.wait()
                time.sleep(0.1)
                self.__updatePower()   
    
    def __updateStats(self):
        while (os.stat(self.inst_file).st_size == 0):
            time.sleep(0.01)
        for c in range (6):
            self.core_info[c] = self.__findStatsByCore(c)

    def __updatePower(self):
        curr_power = self.__findPower()
        tmp_list = self.power_list[1:]
        tmp_list.append(curr_power)
        self.power_list = tmp_list
        self.power = getAverage(self.power_list)

    
    def __findStatsByCore(self, core):
        f = open(self.inst_file, 'r')
        data = f.readlines()
        f.close()
        res = []
        for d in data:
            if "CPU"+str(core) in d:
                res.append(d)
        return res
    
    def __findPower(self):
        f = open(self.power_file, 'r')
        pow = int(f.readline())
        f.close()
        return pow


    def getInstructions(self, core):
        instruc = int(self.core_info[core][0][10:27].replace(".", ''))
        #for l in self.core_info[core]:
        #    print(l)
        return instruc
    
    def getCacheAccesses(self, core):
        refs = int(self.core_info[core][2][10:27].replace(".", ''))
        #for l in self.core_info[core]:
        #    print(l)
        return refs
    
    def getCacheMisses(self,core):
        misses = int(self.core_info[core][1][10:27].replace(".", ''))
        #for l in self.core_info[core]:
        #    print(l)
        return misses

    def getPower(self):
        return self.power
    
    def getEfficiency(self):
        total_instr = 0
        for c in range(6):
            total_instr += self.getInstructions(c)
        return total_instr / (self.refresh * self.power)
        

# mon = Monitor(1)
# mon.start()
# time.sleep(4)
# while True:
#     for c in range(6):
#         print(mon.getInstructions(c))
#     print("***************")
#     time.sleep(1)
