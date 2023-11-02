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

SCRIPTS_DIR="/home/jetson/mitecca/scripts/"

available_apps = ['splash-barnes', 'splash-cholesky', 'splash-lucont', 'splash-ocean', 'splash-radix', 'splash-raytrace',
                  'spec-gcc', 'spec-libquantum', 'spec-omnetpp', 'spec-xalancbmk', 'spec-bzip2', 'spec-sphinx3', 'spec-astar']

tcc = "./tcc"


finished = False




def startFunc(app_str, core):
    str_cmd = "taskset -c " + str(core) + " " + app_str + " " + str(core)
    print(str_cmd)
    command = str_cmd.split(" ")
    ##print(command)
    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    p.wait()
    
def startWorkFunc(app_str, core):
    str_cmd = "taskset -c " + str(core) + " " + app_str + " " + str(core)
    command = str_cmd.split(" ")
    #print(str_cmd)
    if "tcc" in  app_str:
         print(str_cmd)
         p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    else:
        global finished
        while (finished == False):
            print(str_cmd)
            p = subprocess.Popen(command,  stdout=subprocess.PIPE)
            p.wait()
        

def killProc(proc_name):
    str_cmd = "sudo killall " + proc_name
    command = str_cmd.split(" ")
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    p.wait()

def makeThreads(mapping):
    #print("Launching workload")
    a = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[0]), 0))
    b = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[1]), 1))
    c = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[2]), 2))
    d = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[3]), 3))
    e = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[4]), 4))
    t = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[5]), 5))
    t.start()
    a.start()
    b.start()
    c.start()
    d.start()
    e.start()

    # wait for some time before measuring window
    time.sleep(3.5)#(3*random())
    start = timer()
    monitorPower()
    monitorAggregatedIPC(10)
    d.join()
    a.join()
    c.join()
    t.join()
    b.join()
    e.join()
    end = timer()
    #killProc("getpower.sh")
    elapsed = end - start 
    #print(elapsed)
    return elapsed
def applyDVFS(core):
    f = threading.Thread(target=startFunc, args=("./dvfs.sh " + str(core), 0))
    f.start()

def monitorPower():
    print("Monitoring Power")
    m = threading.Thread(target=startFunc, args=("sudo utils/getpower.sh",  0))
    m.start()

def getEnergy(time, ipc):
    #print("Power (W) \t IPC \t Efficiency (IPC/W)")
    f = open("power.out", "r")
    pows = f.readlines()
    sum = 0
    for p in pows:
        sum+=float(p)
    avg = sum/(1000*len(pows))
    f = open("efficiency.out", "a")
    #print(str(avg) + "\t" + str(ipc) + "\t" + str(ipc/avg))
    f.write(str(avg) + "\t" + str(ipc) + "\t" + str(ipc/avg) + "\n")


def getEfficiency(ips):
    #print("Power (W) \t IPS \t Efficiency (IPS/W)")
    f = open("power.out", "r")
    pows = f.readlines()
    sum = 0
    for p in pows:
        sum+=float(p)
    avg = sum/(1000*len(pows))
    efficiency = ips/avg
    f = open("efficiency.out", "a")
    #print(str(avg) + "\t" + str(ips) + "\t" + str(efficiency))
    f.write(str(avg) + "\t" + str(ips) + "\t" + str(efficiency) + "\n")
    return efficiency

def startClean():
    str_cmd = "sudo rm -rf energy.out power.out efficiency.out *.ipc ipc.out"
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()

def restoreFreqs():
    startFunc("utils/setallmax.sh", 0)


def getFullApp(app_str):
    if "spec" in app_str:
        name = SCRIPTS_DIR+"spec.sh " + app_str[5:] 
    elif "splash" in app_str:
        name = SCRIPTS_DIR+app_str[7:]+".sh" 
    else:
        name = app_str
    return name


def monitorAggregatedIPC(duration):
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
   
    # convert datetime obj to string
    RESULTS_FOLDER = "results/" + str(current_datetime)

    str_cmd = "mkdir " + RESULTS_FOLDER
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()
    print("Monitoring IPC")
    str_cmd = "utils/getIPC.sh " + RESULTS_FOLDER +"/aggregatedIPC.log " + str(duration)
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()
    print("Finished monitoring window. Waiting for current programs to finish")
    global finished
    finished = True
    killProc("getpower.sh")


def parseIPCFile():
    ipc_file = open("ipc.out", "r")
    ipcs = ipc_file.readlines()
    sum = 0
    for line in ipcs:
        ipc_str = line[-33:-24].replace(",", ".")
        sum += float(ipc_str)
    avg = sum / len(ipcs)
    return avg

def parseIPSfromFile():
    ipc_file = open("ipc.out", "r")
    ipss = ipc_file.readlines()
    sum = 0
    for line in ipss:
        ips_str = line[24:40].replace(".", '')
        sum += int(ips_str)
    ips = float(sum/(0.1*len(ipss)))
    print(ips)
    return ips

def run_experiment(withDVFS, mapping, iters):
    startClean()
    print("Current mapping: " + str(mapping))
    attack_core = -1
    for i in range (iters):
        if (withDVFS):
            for c in range(len(mapping)):
                if "tcc" in mapping[c]:
                    attack_core = c
                    print("Core " + str(c) + ": DVFS is ON ")
            if (attack_core < 0):
                print("Something horrible happened")
                return 0
            applyDVFS(attack_core)
        #start the workload
        elapsed = makeThreads(mapping)

        killProc("tcc")
        if (withDVFS):
            killProc("dvfs.sh")
        ips = parseIPSfromFile()
        efficiency = getEfficiency(ips)
        #getEnergy(elapsed, ipc)
        restoreFreqs()
        global finished
        finished = False
    return  efficiency

def generateApps():
    apps = []
    attack_core = randrange(6)
    for i in range(6):
        apps.append(available_apps[randrange(len(available_apps))])
    apps[randrange(6)] = tcc
    return apps


def findMotiv():
    found = False
    tries = 0
    while not found:
        restoreFreqs()
        time.sleep (2)
        mapping = generateApps()
        print("trying..")
        print(mapping)
        baseline = run_experiment(False, mapping, 1)
        print("baseline efficiency = " + str(baseline))
        time.sleep(2)
        eff_dvfs = run_experiment(True, mapping, 1)
        print("WithDVFS = " + str(eff_dvfs))
        loss = (eff_dvfs/baseline) - 1
        print("Loss = " + str(loss))
        if (loss < -0.2 ):
            found = True
        tries +=1
        if (tries == 200):
            print("No nice scenario found, sorry")
            break
    print("Found!")
    print(mapping)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Main experiment script.')
    parser.add_argument("-f", '--dvfs', action='store_true',default=False,
                    help='Lunch programs with DVFS on the attacking core')
    #parser.add_argument("t-", '--timeout', action='store_true',default=False,
    #                help='Lunch programs with DVFS on the attacking core')
    args = parser.parse_args()
    startClean()

    withDVFS = args.dvfs
    findMotiv()
    # mapping_baseline =  ['splash-barnes', 'spec-libquantum', 'spec-libquantum', './tcc', 'splash-raytrace', 'splash-ocean']
    # mapping_scenario1 = ['splash-barnes', './tcc', 'spec-libquantum', 'spec-libquantum', 'splash-raytrace', 'splash-ocean']
    # mapping_scenario2 = ['splash-barnes', 'splash-raytrace', 'spec-libquantum', './tcc', 'spec-libquantum',  'splash-ocean']
    # mapping_scenario3 = ['spec-libquantum', 'splash-barnes', 'splash-ocean', './tcc', 'splash-raytrace', 'spec-libquantum']
    # mapping_scenario4 = ['splash-barnes', 'splash-ocean', 'spec-libquantum', './tcc',  'spec-libquantum', 'splash-raytrace']
    # mapping_scenario5 = ['splash-barnes', './tcc', 'splash-ocean', 'spec-libquantum',  'splash-raytrace', 'spec-libquantum']
    # mapping_scenario6 = ['splash-barnes', './tcc', 'splash-raytrace', 'spec-libquantum',   'spec-libquantum', 'splash-ocean']
    
    
    # mapping = mapping_scenario6
    # run_experiment(withDVFS, mapping, 5)

   




