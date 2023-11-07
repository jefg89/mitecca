from monitor import *

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

available_apps = ['splash-barnes', 'splash-cholesky', 'splash-lu', 'splash-ocean', 'splash-radix', 'splash-raytrace',
                  'spec-gcc', 'spec-milc', 'spec-omnetpp', 'spec-xalancbmk', 'spec-bzip2', 'spec-sphinx3', 'spec-astar']

tcc = "./tcc"


finished = False

mon = Monitor(1)

def runProc(app_str):
    command = app_str.split(" ")
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
    #creating threads
    a = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[0]), 0))
    b = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[1]), 1))
    c = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[2]), 2))
    d = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[3]), 3))
    e = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[4]), 4))
    f = threading.Thread(target=startWorkFunc, args=(getFullApp(mapping[5]), 5))
    print("Launching workload")

    a.start()
    b.start()
    c.start()
    d.start()
    e.start()
    f.start()

    return a,b,c,d,e,f


def applyDVFS(core):
    f = threading.Thread(target=runProc, args=("./dvfs.sh "))
    f.start()


def startClean():
    str_cmd = "sudo rm -rf *.ipc *.out"
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()

def restoreFreqs():
    runProc("utils/setallmax.sh")


def getFullApp(app_str):
    if "spec" in app_str:
        name = SCRIPTS_DIR+"spec.sh " + app_str[5:] 
    elif "splash" in app_str:
        name = SCRIPTS_DIR+app_str[7:]+".sh" 
    else:
        name = app_str
    return name




def getProcessName(app_str):
    if "spec" in app_str:
        if "xalan" in app_str:
            name = "Xalan_base.lnx64-gcc"
        elif "sphinx" in app_str:
            name = "sphinx_livepretend_base.lnx64-gcc"
        else:
            name = app_str[5:] +"_base.lnx64-gcc"
    elif "splash" in app_str:
        name = app_str[7:].upper()
    else:
        name = "tcc"
    
    return name

def generateApps():
    apps = []
    attack_core = randrange(6)
    while len(apps) < 6:
        candidate = available_apps[randrange(len(available_apps))]
        if candidate not in apps:
            apps.append(candidate)
    apps[randrange(6)] = tcc
    return apps

def containsMap(map_list, map):
    for m in map_list:
        if m == map:
            return True
    return False

def generateVariants(mapping, N):
    unique = []
    unique.append(mapping)
    found_maps = 0
    while found_maps < N:
        tmp_map = list(mapping)
        random.shuffle(tmp_map)
        if not containsMap(unique, tmp_map):
            unique.append(tmp_map)
            found_maps+=1
    return unique
   

def getProcessNamesFromMap(mapping):
    procs = []
    for app in mapping:
        procs.append(getProcessName(app))
    return procs



def run_experiment(name, withDVFS, mapping, iters, delay):
    global log_file
    #*******************************************************************
    of = open(RESULTS_FOLDER + "/" + name + ".out", 'a')
    # for x in range(6):
    #     pref = "C" + str(x)+ "_"
    #     of.write(pref + "instr \t" + pref + "acces \t" + pref + "misses \t")
    # of.write("Efficiency(I/J)\n")
    #*********************************************************************  

    print("Current mapping: " + str(mapping))
    log_file.write("Executing Current mapping: \n" + str(mapping) + "\n")
    log_file.write("Window length = 1s. Random Delay = " + str(delay) + "\n")
    attack_core = -1
    for i in range (iters):
        #Check wheter we need to apply dvfs
        if (withDVFS):
            for c in range(len(mapping)):
                if "tcc" in mapping[c]:
                    attack_core = c
                    print("Core " + str(c) + ": DVFS is ON ")
                    log_file.write("Core " + str(c) + ": DVFS is ON \n")
            if (attack_core < 0):
                print("Something horrible happened")
                return 0
            applyDVFS(attack_core)
        else:
            log_file.write("DVFS = OFF \n")
       
        #start the workload
        ta,tb,tc,td,te,tf = makeThreads(mapping)
        #wait for a window and record
        time.sleep(delay)
        
        #logging metrics
        print("Measurement triggered")
        instr = 0
        refs = 0
        misses = 0
        for c in range(6):
            of.write(str(mon.getInstructions(c))+"\t")
            of.write(str(mon.getCacheAccesses(c))+"\t")
            of.write(str(mon.getCacheMisses(c))+"\t")
            #instr.append(mon.getInstructions(c))
            #refs.append(mon.getCacheAccesses(c))
            #misses.append(mon.getCacheMisses(c))
        #eff = mon.getEfficiency()
        of.write(str(mon.getEfficiency())+"\n")
        #wait for the threads to finish
        global finished
        finished = True
        ta.join()
        tb.join()
        tc.join()
        td.join()
        te.join()
        tf.join()
        #kill the eternal attacker
        killProc("tcc")
        if (withDVFS):
            killProc("dvfs.sh")
            time.sleep(2)
            restoreFreqs()
        #leave everything ready for next iteration
        finished = False
    of.close()
    #mon.stop()
    print("Experiment finished successfully")


def getPIDs(mapping):
    procs = getProcessNamesFromMap(mapping)
    pids = []
    for ps in procs:
        found = False
        str_cmd = "pidof " + ps
        command = str_cmd.split(" ")
        print(str_cmd)
        while not found:
                p = subprocess.Popen(command,  stdout=subprocess.PIPE)
                p.wait()
                ans = p.stdout.readline()
                try:
                    a = int(ans.decode("utf-8")) + 1 - 1
                    found = True
                    pids.append(a)

                except:
                    time.sleep(0.005)

    return pids

def setAffinity(pid, core):
    runProc("taskset -cp " + str(core) + " " + str(pid))


def executeMigration(mapping, newmap, pids):
    tmp_pids = list(pids)
    for idx in range(len(mapping)):
        pid = pids[idx]
        new_idx = newmap.index(mapping[idx])
        if new_idx != idx:
            setAffinity(pid, new_idx)
            pass
            tmp_pids[new_idx] = pids[idx]
    return tmp_pids  

def run_simple(mapping, migration):
    print("Current mapping: " + str(mapping))
    print("Migration mapping: " + str(migration))
    ta,tb,tc,td,te,tf = makeThreads(mapping)
    
    pids = getPIDs(mapping)
    print(pids)
    pids = executeMigration(mapping, migration, pids)
    print(pids)
    

    global finished
    finished = True
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()
    killProc("tcc")
    print("Experiment finished successfully")



if __name__ == "__main__":
    startClean()
    # mon.start()
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # #directory creation TODO: move to a function that returns the file
    # #*******************************************************************
    RESULTS_FOLDER = "results/" + "training_" + str(current_datetime)
    # str_cmd = "mkdir " + RESULTS_FOLDER
    # command = str_cmd.split(" ")
    # p = subprocess.Popen(command)
    # p.wait()
    # #***********************************************************
    # #test 
    # global log_file
    # log_file = open(RESULTS_FOLDER +"/experiment.log", "w")
    
    iters = 1
    num_bases = 20
    map_variants = 8
    runs_per_map = 10


    testmap = generateApps()
    migration = generateVariants(testmap, 1)
    print(testmap)
    print(migration[1])


    # print(testmap)
    # print(getProcessNamesFromMap(testmap))
    # print(migration[1])
    run_simple(testmap, migration[1])

    



    # for x in range(num_bases):
    #     base_mapping = generateApps()
        
    #     #generating variant mappings
    #     maps = generateVariants(base_mapping, map_variants)
    #     for m in maps:
    #         log_file.write(str(m)+ "\n")
        
        
    #     #directory creation TODO: move to a function 
    #     #*******************************************************************
    #     if not os.path.isdir(RESULTS_FOLDER + "/base_" + f"{x:02}"):
    #         # directory does not exist
    #         str_cmd = "mkdir " + RESULTS_FOLDER + "/base_" + f"{x:02}"
    #         command = str_cmd.split(" ")
    #         p = subprocess.Popen(command)
    #         p.wait()
    #     #*******************************************************************

    #     SUBFOLDER = "/base_" + f"{x:02}"
        
    #     for id in range (runs_per_map):
    #         #directory creation TODO: move to a function 
    #         #*******************************************************************
    #         if not os.path.isdir(RESULTS_FOLDER +  SUBFOLDER + "/run_" + f"{id:02}"):
    #             # directory does not exist
    #             str_cmd = "mkdir " + RESULTS_FOLDER + SUBFOLDER + "/run_" + f"{id:02}"
    #             command = str_cmd.split(" ")
    #             p = subprocess.Popen(command)
    #             p.wait()
    #         #*******************************************************************
           
    #         r_delay = 10 * random.random()
            
    #         #Run baseline map with and without DVFS 
    #         run_experiment(SUBFOLDER + "/run_" + f"{id:02}" + "/baseline", False, base_mapping, iters, r_delay)
    #         run_experiment(SUBFOLDER + "/run_" + f"{id:02}" + "/baseline_DVFS", True, base_mapping, iters, r_delay)
    #         #then run all the variants with DVFS=ON
    #         log_file.write("Executing variants of mapping \n")
    #         for r in range(1,len(maps)):
    #             run_experiment(SUBFOLDER + "/run_" + f"{id:02}" + "/variants", True, maps[r], iters, r_delay)
            
    #mon.stop()



