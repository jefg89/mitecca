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

#available_apps = ['splash-barnes', 'splash-cholesky', 'splash-lu', 'splash-ocean', 'splash-radix', 'splash-raytrace',
available_apps = ['spec-gcc', 'spec-milc', 'spec-bzip2', 'spec-sphinx3', 'spec-astar', 'spec-lbm',
                  'spec-bwaves', 'spec-mcf', 'spec-zeusmp',  'spec-namd', 'spec-h264ref', 'spec-gobmk']
#'spec-omnetpp'
#'spec-povray', 'spec-gromacs', 'spec-cactusADM',
tcc = "./tcc"


finished = False


def runProc(app_str):
    command = app_str.split(" ")
    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    p.wait()
    
def startWorkFunc(app_name, core):
    app_str = getFullApp(app_name)
    str_cmd = "taskset -c " + str(core) + " " + app_str + " " + str(core)
    command = str_cmd.split(" ")
    #print(str_cmd)
    if "tcc" in  app_str:
         #print(str_cmd)
         p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    else:
        #print(str_cmd)
        p = subprocess.Popen(command,  stdout=subprocess.PIPE)
        p.wait()
        global mapping
        core = -1
        app_short = app_name[5:]
        for idx in range(len(mapping)):
            if app_short in mapping[idx]:
                core = idx
        
        mapping[core] = mapping[core]+"*"
        print("[Core " + str(core) +"]: " + app_name + " finished execution!" )
        



        

def killProc(proc_name):
    str_cmd = "sudo killall " + proc_name
    command = str_cmd.split(" ")
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    p.wait()
    

def makeThreads(mapping):
    #creating threads
    a = threading.Thread(target=startWorkFunc, args=(mapping[0], 0))
    b = threading.Thread(target=startWorkFunc, args=(mapping[1], 1))
    c = threading.Thread(target=startWorkFunc, args=(mapping[2], 2))
    d = threading.Thread(target=startWorkFunc, args=(mapping[3], 3))
    e = threading.Thread(target=startWorkFunc, args=(mapping[4], 4))
    f = threading.Thread(target=startWorkFunc, args=(mapping[5], 5))
    print("Launching workload")

    a.start()
    b.start()
    c.start()
    d.start()
    e.start()
    f.start()

    return a,b,c,d,e,f




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

def generateVariant(mapping):
    tmp_map = list(mapping)
    random.shuffle(tmp_map)
    return tmp_map

def getProcessNamesFromMap(mapping):
    procs = []
    for app in mapping:
        procs.append(getProcessName(app))
    return procs





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
    cmd_str = "taskset -cp " + str(core) + " " + str(pid)
    command = cmd_str.split(" ")    
    p = subprocess.Popen(command,  stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if p.stderr.readlines():
        return False
    else:
        p.wait()
        return True
    


def executeMigration(newmap, pids):
    global mapping
    print("[Migration:] Moving apps to follow new mapping:")
    print(newmap)
    tmp_pids = list(pids)
    for idx in range(len(mapping)):
        pid = pids[idx]
        try:
            new_idx = newmap.index(mapping[idx])
            if new_idx != idx:
                tmp_pids[new_idx] = pids[idx]
        except:
            #remove the * of app name for comparison
            new_idx = newmap.index(mapping[idx][:-1])
            newmap[new_idx] = newmap[new_idx] +"*"
            tmp_pids[new_idx] = -1        
    mapping = newmap
    return tmp_pids  


def saveTraces(of, original_map, before_mig):
    for x in range(len(mapping)):
        if ("*" not in mapping[x]):
            id = original_map.index(mapping[x])
        else:
            id = -1
        of.write(str(id)+"\t") 
    if before_mig:
        for c in range(6):
            of.write(str(mon.getInstructions(c))+"\t")
            of.write(str(mon.getCacheAccesses(c))+"\t")
            of.write(str(mon.getCacheMisses(c))+"\t")
        of.write(str(mon.getEfficiency())+"\t")
    else:
        of.write(str(mon.getEfficiency())+"\n")



def run_simple(mapping):
    start = timer()
    print("Current mapping: " + str(mapping))
    ta,tb,tc,td,te,tf = makeThreads(mapping)
    global finished
    finished = True
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()
    end = timer()
    elapsed = end - start
    killProc("tcc")
    print("Experiment finished successfully") 
    print("Total execution time = ", str(round(elapsed,2)) + "s")   


def run_experiment(base_map, delay):
    global log_file
    global mapping
    mapping = list(base_map)
    
    of = open(RESULTS_FOLDER + "/stats.out", 'a')

    print("Current mapping: " + str(mapping))
    log_file.write("Executing Current mapping: \n" + str(mapping) + "\n")
    log_file.write("Window length = 1s. Random Delay = " + str(delay) + "\n")
    attack_core = -1
    start = timer()
    ta,tb,tc,td,te,tf = makeThreads(mapping)
    pids = getPIDs(mapping)
    print(pids)
    
    #new random mapping
    migration = generateVariant(mapping)
    #wait randoy delay before trigger measurement
    time.sleep(delay)
    #record pre migration traces
    mon.record()
    #wait a little for the the trace to be recorded
    while not mon.isdone():
        time.sleep(0.01)

    saveTraces(of, base_map, before_mig=True)
    
    #apply dvfs
    for c in range(len(migration)):
        if "tcc" in migration[c]:
            attack_core = c
    #print("attack core is "+ str(attack_core))
    applyDVFS(str(attack_core))
    #then migrate
    pids = executeMigration(migration, pids)
    #and start recording again
    mon.record()
    print(pids)
    while not mon.isdone():
        time.sleep(0.01)

    saveTraces(of, base_map, before_mig=False)

    #umm let's do it again at least of couple of times
    #but do not apply dvfs, since we are doing so already
  
    for times in range(5):
        #first generate random variant
        migration = generateVariant(mapping)
        #trigger recording
        mon.record()
        #wait a little for the the trace to be recorded
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=True)
        #then migrate
        pids = executeMigration(migration, pids)
        #and start recording again
        mon.record()
        print(pids)
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=False)
    
    #not needed anymore
    #global finished
    #finished = True
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()
    end = timer()
    elapsed = end - start
    killProc("tcc")
    print("Experiment finished successfully") 
    print("Total execution time = ", str(round(elapsed,2)) + "s")   
    killProc("dvfs.sh")
    time.sleep(1)
    restoreFreqs()

def run_training():
    global current_datetime
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # #directory creation TODO: move to a function that returns the file
    # #*******************************************************************
    global RESULTS_FOLDER
    RESULTS_FOLDER = "results/" + "training_" + str(current_datetime)
    str_cmd = "mkdir " + RESULTS_FOLDER
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()
    #***********************************************************

    
    global log_file
    log_file = open(RESULTS_FOLDER +"/experiment.log", "w")
    
    num_bases = 20
    runs_per_map = 5 

    for x in range(num_bases):
        #base_mapping = ['./tcc', 'spec-gobmk', 'spec-lbm', 'spec-sphinx3', 'spec-namd', 'spec-milc']
        base_mapping = generateApps()        
        for id in range (runs_per_map):           
            r_delay = 1.5*random.random()
            #Run baseline map with and without DVFS 
            run_experiment(base_mapping, r_delay)
            #with DVFS on base here



def applyDVFS(core):
    print("Applying DVFS to core: " + str(core))
    f = threading.Thread(target=startDVFS, args=(core))
    f.start()


def startDVFS(core):
    str_cmd ="./dvfs.sh " + str(core)
    #print(str_cmd)
    command = str_cmd.split(" ")
    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    p.wait()

if __name__ == "__main__":
    mon = Monitor("trigger", 1)
    startClean()
    mon.start()
    run_training() 
    mon.stop()
    #try this one  ['spec-namd', 'spec-omnetpp', './tcc', 'spec-bwaves', 'spec-bzip2', 'spec-mcf']


