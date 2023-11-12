import threading
import sys
import os
import time
from timeit import default_timer as timer
import subprocess

import argparse

SCRIPTS_DIR="/home/jetson/mitecca/scripts/"

available_apps = ['splash-barnes', 'splash-cholesky', 'splash-lucont', 'splash-ocean', 'splash-radix', 'splash-raytrace'
                  'spec-gcc', 'spec-libquantum', 'spec-omnetpp', 'spec-xalancbmk']

tcc = "./tcc"



def startFunc(app_str, core):
    str_cmd = "taskset -c " + str(core) + " " + app_str + " " + str(core)
    print(str_cmd)
    command = str_cmd.split(" ")
    #print(command)
    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    if ("tcc" not in app_str):
        p.wait()
    


def killProc(proc_name):
    str_cmd = "sudo killall " + proc_name
    command = str_cmd.split(" ")
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    p.wait()

def makeThreads(attack_core):
    a = threading.Thread(target=startFunc, args=(getFullApp('splash-raytrace'), 5))
    b = threading.Thread(target=startFunc, args=(getFullApp('splash-ocean'), 2))
    c = threading.Thread(target=startFunc, args=(getFullApp('splash-radix'), 1))
    d = threading.Thread(target=startFunc, args=(getFullApp('splash-barnes'), 4))
    t = threading.Thread(target=startFunc, args=(tcc, attack_core))
    t.start()
    a.start()
    b.start()
    c.start()
    d.start()
    a.join()
    b.join()
    c.join()
    d.join()
    t.join()

def applyDVFS(core):
    f = threading.Thread(target=startFunc, args=("./dvfs.sh " + str(core), 0))
    f.start()

def monitorPower():
    m = threading.Thread(target=startFunc, args=("sudo utils/getpower.sh",  0))
    m.start()

def getEnergy(time):
    #print("Power (W) \t Makespan (s) \t Energy (J)")
    f = open("power.out", "r")
    pows = f.readlines()
    sum = 0
    for p in pows:
        sum+=float(p)
    avg = sum/(1000*len(pows))
    f = open("energy.out", "a")
    f.write(str(avg) + "\t" + str(time) + "\t" + str(avg * time) + "\n")

def startClean():
    str_cmd = "sudo rm -rf energy.out power.out"
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()

def restoreFreqs():
    startFunc("utils/setallmax.sh", 0)


def getFullApp(app_str):
    if "spec" in app_str:
        name = SCRIPTS_DIR+"spec.sh " + app_str[5:] 
    else:
        name = SCRIPTS_DIR+app_str[7:]+".sh" 
    return name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Main experiment script.')
    parser.add_argument("-f", '--dvfs', action='store_true',default=False,
                    help='Lunch programs with DVFS on the attacking core')
    args = parser.parse_args()
    startClean()
    attack_core = 3
    #actually run the thing
    for i in range (1):
        if (args.dvfs):
            print("DVFS is ON")
            applyDVFS(attack_core)
        start = timer()
        monitorPower()
        makeThreads(attack_core)
        end = timer()
        killProc("getpower.sh")
        elapsed = end - start 
        print(elapsed)
        killProc("tcc")
        if (args.dvfs):
            killProc("dvfs.sh")
        getEnergy(elapsed)
        restoreFreqs()
