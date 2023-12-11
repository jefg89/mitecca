from config import *
from monitor import *
from retthreading import *
from mitecca import *

from policies import *



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

lock = threading.Lock()
end_of_experiment = False


available_apps = ['spec-gcc', 'spec-milc', 'spec-bzip2', 'spec-sphinx3', 'spec-astar', 'spec-lbm',
                  'spec-bwaves', 'spec-mcf', 'spec-zeusmp',  'spec-namd', 'spec-h264ref', 'spec-gobmk',
                  'spec-povray', 'spec-gromacs', 'spec-cactusADM', 'spec-omnetpp', 'spec-hmmer', 'spec-leslie3d']
                  #'splash-barnes', 'splash-cholesky', 'splash-lu', 'splash-ocean', 'splash-radix', 'splash-raytrace',
                  #'splash-fmm']
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
        
        with lock:
            idcore = mapping.index(app_name)
            mapping[idcore] = mapping[idcore]+"*"
        print("[Core " + str(idcore) +"]: " + app_name + " finished execution!" )
        



        

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


def waitForThreads(a, b, c, d, e, f):
    a.join()
    b.join()
    c.join()
    d.join()
    e.join()
    f.join()
    global end_of_experiment
    end_of_experiment = True
    print("END!")


def startClean():
    str_cmd = "sudo rm -rf *.ipc *.out *.tmp"
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



def getPIDThread(proc):
    found = False
    str_cmd = "taskset -c 0 pidof " + proc
    command = str_cmd.split(" ")
    pid = -1
    #print(str_cmd)
    tries = 0
    if "CHOLESKY" in proc:
        time.sleep(1)
    while not found:
        p = subprocess.run(command,capture_output=True)
        ans = p.stdout
        try:
            a = int(ans.decode("utf-8")) + 1 - 1
            found = True
            pid = a
        except:
            tries+=1
            time.sleep(0.005)
            if tries >= 100:
                print("Warning: Process ", proc, " has probably finished")
                found = True
    return pid


#this is an overkill, I am not sorry.
def getPIDs(mapping):
    procs = getProcessNamesFromMap(mapping)
    #print(procs)
    pids = [-1,-1,-1,-1,-1,-1]
    a = RetThread(target=getPIDThread, args=(procs[0],))
    b = RetThread(target=getPIDThread, args=(procs[1],))
    c = RetThread(target=getPIDThread, args=(procs[2],))
    d = RetThread(target=getPIDThread, args=(procs[3],))
    e = RetThread(target=getPIDThread, args=(procs[4],))
    f = RetThread(target=getPIDThread, args=(procs[5],))
    #print("[Thread team]: getting pids in parallel")
    a.start()
    b.start()
    c.start()
    d.start()
    e.start()
    f.start()

    pids[0] = a.join()
    pids[1] = b.join()
    pids[2] = c.join()
    pids[3] = d.join()
    pids[4] = e.join()
    pids[5] = f.join()

    return pids

def getCluster(core):
    return  int((core == 1 ) | (core == 2))
def setAffinity(pid, core):
    cmd_str = "taskset -cp " + str(core) + " " + str(pid)
    command = cmd_str.split(" ")    
    p = subprocess.Popen(command,  stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if p.stderr.readlines():
        return False
    else:
        p.wait()
        return True
   
def applyDVFS(core):
    f = threading.Thread(target=startDVFS, args=(core,))
    f.start()


def startDVFS(core):
    str_cmd ="./utils/dvfs.sh " + str(core)
    #print(str_cmd)
    command = str_cmd.split(" ")
    p = subprocess.Popen(command,  stdout=subprocess.PIPE)
    p.wait()


def executeMigration(newmap, pids):
    global mapping
    print(newmap)
    tmp_pids = list(pids)
    #Only apply migration if the new candidate is different than current mapping
    if (newmap != mapping):
        #check each app for its new core
        for idx in range(len(mapping)):
            pid = pids[idx]
            #the application might have finished, so check first if it exists still
            try:
                new_idx = newmap.index(mapping[idx])
                # let's check if it needs to be moved
                if new_idx != idx:
                    #if so then save the new pid in the corresponding core position
                    tmp_pids[new_idx] = pid
                    #and move it
                    setAffinity(pid, new_idx)
            #if the app finished already
            except:
                #remove the * of app name for comparison
                new_idx = newmap.index(mapping[idx][:-1])
                #and add it again in the new mapping
                newmap[new_idx] = newmap[new_idx] +"*"
                #then set the pid to undefined (-1)
                tmp_pids[new_idx] = -1
        #finally make the current mapping as the new one
        with lock:    
            mapping = newmap
    return tmp_pids  


def saveTraces(of, original_map, before_mig, dvfs):
    for c in range(6):
        of.write(str(dvfs[c]) +"\t")
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



def run_simple(base_map, workdir=None):
    global mapping
    mapping = list(base_map)
    if (workdir!=None):
        mon.setworkdir(workdir)
    mon.start()
    print("Current mapping: " + str(base_map))
    ta,tb,tc,td,te,tf = makeThreads(base_map)
    start = timer()
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()
    mon.stop()
    end = timer()
    elapsed = end - start
    killProc("tcc")
    print("Experiment finished successfully") 
    print("Total execution time = ", str(round(elapsed,2)) + "s")
    return elapsed



def run_simple_dvfs_after_delay(base_map, delay, workdir=None):
    global mapping
    mapping = list(base_map)
    if (workdir!=None):
        mon.setworkdir(workdir)
    start = timer()
    mon.start()
    print("Current mapping: " + str(base_map))
    ta,tb,tc,td,te,tf = makeThreads(base_map)
    # wait for delay before applying dvfs
    print("Waiting before applying DVFS")
    time.sleep(delay)
    # now let's apply dvfs where the attacker is 

    #apply dvfs
    attack_core = -1
    for c in range(len(mapping)):
        if "tcc" in mapping[c]:
            attack_core = c
    print("Applying DVFS to core: " + str(attack_core))
    applyDVFS(attack_core)
    print("Waiting for workload to finish")
    #and now let's wait for the workload to finish
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()

    mon.stop()
    end = timer()
    elapsed = end - start
    print("Experiment finished successfully")
    print("Total execution time = ", str(round(elapsed,2)) + "s")
    killProc("tcc")   
    time.sleep(1)
    restoreFreqs() 
    
def run_simple_migrate_dvfs(base_map, delay, migration, workdir=None):
    global mapping
    mapping = list(base_map)
    if (workdir!=None):
        mon.setworkdir(workdir)
    start = timer()
    mon.start()
    print("Current mapping: " + str(base_map))
    ta,tb,tc,td,te,tf = makeThreads(base_map)
    pids = getPIDs(mapping)
    print(pids)
    # wait for delay before applying dvfs
    print("Waiting before applying DVFS")
    time.sleep(delay)
    #now let's apply dvfs where the attacker is 
    #apply dvfs
    attack_core = -1
    for c in range(len(migration)):
        if "tcc" in migration[c]:
            attack_core = c
    print("Applying DVFS to core: " + str(attack_core))
    applyDVFS(attack_core)

    #then migrate
    pids = executeMigration(migration, pids)
    print("Waiting for workload to finish")
    #and now let's wait for the workload to finish
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()

    mon.stop()
    end = timer()
    elapsed = end - start
    print("Experiment finished successfully")
    print("Total execution time = ", str(round(elapsed,2)) + "s")
    killProc("tcc")   
    killProc("dvfs.sh")
    time.sleep(1)
    restoreFreqs() 
    
    
def run_with_policy(base_map, delay, Policy, workdir=None):
    global mapping
    mapping = list(base_map)
  
    attack_core = base_map.index("./tcc")
    if (workdir!=None):
        mon.setworkdir(workdir)
    start = timer()
    mon.start()
    #time.sleep(1)
    print("Current mapping: " + str(base_map))
    ta,tb,tc,td,te,tf = makeThreads(base_map)
    pids = getPIDs(mapping)
    waiter =  threading.Thread(target=waitForThreads, args=(ta,tb,tc,td,te,tf,))
    waiter.start()
    print(pids)
    # wait for delay before applying dvfs
    print("Waiting from detector")
    time.sleep(delay)

    prev_cluster = -1
    dvfs = 0
    ## replace wiith while
    global end_of_experiment 
    while not end_of_experiment:
        start_=timer()
        current_features = []
        for x in range(6):
            current_features.append(mon.getInstructions(x))
            current_features.append(mon.getCacheAccesses(x))
            current_features.append(mon.getCacheMisses(x))                        
        current_efficiency = mon.getEfficiency()
        #print(current_features)
        #print(current_efficiency)
        #print("original ", base_map)
        #print("current ", mapping)
        if (attack_core == 1) | (attack_core == 2): 
            curr_dvfs = [1,0,0,1,1,1]
        else: 
            curr_dvfs = [1,0,0,1,1,1]
        if (dvfs == 0):
            curr_dvfs = [0,0,0,0,0,0]
        #***************************************
        # Apply the policy here
        with lock:
            #(curr_map, original_map, curr_dvfs, current_features, current_efficiency, attack_core)
            migration, pred_eff = Policy.executePolicy(mapping, base_map, curr_dvfs, current_features, current_efficiency, attack_core)
        #
        # **************************************

       
        print("decision from policy : ", migration, "with eff: ", pred_eff)
        #migration = fixedCoreProxy(mapping)

        #now let's apply dvfs where the attacker is 
        #apply dvfs
        for c in range(len(migration)):
            if "tcc" in migration[c]:
                attack_core = c
        print("Applying DVFS to core: " + str(attack_core))
        curr_cluster = getCluster(attack_core)
        
        if (curr_cluster != prev_cluster):
            killProc("dvfs.sh")
            time.sleep(0.1)
            restoreFreqs()
            #print("prev ", prev_cluster)
            #print("current = ", curr_cluster)
            applyDVFS(attack_core)
        prev_cluster = curr_cluster
        dvfs = 1
        #then migrate
        pids = executeMigration(migration, pids)
        #end_=timer()
        #print("time is ", end_-start_)
        #time.sleep(0.5)
        #if diff < 1:
        print("**************  Current map: ", mapping, "*******************")
        time.sleep(1)
        #after_eff =  mon.getEfficiency()/1e9
        #print("input efficiency was: ", current_efficiency/1e9,
        #      "Prediction was: ", pred_eff, 
        #      "After efficiency is: ", after_eff)
    
    print("Finishing")
        #and now let's wait for the workload to finish

    mon.stop()
    end = timer()
    elapsed = end - start
    print("Experiment finished successfully")
    print("Total execution time = ", str(round(elapsed,2)) + "s")
    killProc("tcc")   
    killProc("dvfs.sh")
    time.sleep(1)
    restoreFreqs()
    end_of_experiment = False
    return round(elapsed,2)




def run_experiment(base_map, delay):
    global log_file
    global mapping

    mapping = list(base_map)
    of = open(WORK_FOLDER + "/stats.out", 'a')

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
    curr_dvfs = [0,0,0,0,0,0]

    saveTraces(of, base_map, before_mig=True, dvfs=curr_dvfs)
    
    #apply dvfs
    for c in range(len(migration)):
        if "tcc" in migration[c]:
            attack_core = c
            curr_cluster = getCluster(attack_core)
    for c in range(6):
        if getCluster(c) == curr_cluster:
            curr_dvfs[c] = 1
        else:
            curr_dvfs[c] = 0
    log_file.write("[DVFS]: Applying DVFS to core " + str(attack_core) + "\n")

    prev_cluster = curr_cluster

    #then migrate
    log_file.write("[Migration:] Moving apps to follow new mapping:" + str(migration) + "\n")
    pids = executeMigration(migration, pids)
    #and start recording again
    mon.record()
    print(pids)
    while not mon.isdone():
        time.sleep(0.01)

    saveTraces(of, base_map, before_mig=False, dvfs=curr_dvfs)

    #umm let's do it again at least of couple of times
    #but do not apply dvfs, since we are doing so already
  
    for times in range(10):
        #first generate random variant
        migration = generateVariant(mapping)
        #trigger recording
        mon.record()
        #wait a little for the the trace to be recorded
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=True, dvfs=curr_dvfs)
        #Now apply DVFS
        for c in range(len(migration)):
            if "tcc" in migration[c]:
                attack_core = c
                curr_cluster = getCluster(attack_core)
        for c in range(6):
            if getCluster(c) == curr_cluster:
                curr_dvfs[c] = 1
            else:
                curr_dvfs[c] = 0        
        if prev_cluster != curr_cluster:
            killProc("dvfs.sh")
            time.sleep(0.1)
            restoreFreqs()
            applyDVFS(attack_core)
        prev_cluster = curr_cluster
        log_file.write("[DVFS]: Applying DVFS to core " + str(attack_core) + "\n")
        #then migrate
        log_file.write("[Migration:] Moving apps to follow new mapping:" + str(migration) + "\n")
        pids = executeMigration(migration, pids)
        #and start recording again
        mon.record()
        print(pids)
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=False, dvfs=curr_dvfs)

    # barrier here, waiting for apps to finish    
    ta.join()
    tb.join()
    tc.join()
    td.join()
    te.join()
    tf.join()
    end = timer()
    elapsed = end - start
    print("Experiment finished successfully")
    log_file.write("Experiment finished successfully\n") 
    print("Total execution time = ", str(round(elapsed,2)) + "s")
    log_file.write("Total execution time = " + str(round(elapsed,2)) + "s\n") 
    killProc("tcc")   
    killProc("dvfs.sh")
    time.sleep(1)
    restoreFreqs()
    

def run_training():
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # #directory creation TODO: move to a function that returns the file
    # #*******************************************************************
    global WORK_FOLDER
    WORK_FOLDER = RESULTS_FOLDER + "training_" + str(current_datetime)
    str_cmd = "mkdir " + WORK_FOLDER
    command = str_cmd.split(" ")
    p = subprocess.Popen(command)
    p.wait()
    #***********************************************************

    
    global log_file
    log_file = open(WORK_FOLDER +"/experiment.log", "w")
    
    num_bases = 100
    runs_per_map = 5
    
    global mon
    mon = Monitor("trigger", 1)
    mon.start()
    for x in range(num_bases):
        #base_mapping = ['./tcc', 'spec-lbm', 'spec-astar', 'spec-bzip2', 'spec-gcc', 'spec-bwaves']
        base_mapping = generateApps()        
        for id in range (runs_per_map):           
            r_delay = 5*random.random()
            #Run baseline map with and without DVFS 
            run_experiment(base_mapping, r_delay)
            #with DVFS on base here
    mon.stop()
    log_file.close()




def eval_run_sota(premaps=None):
    global mon
    mon = Monitor("auto", refresh_rate= 1, logging=True, workdir="./results/")
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    WORK_FOLDER = RESULTS_FOLDER + "sota_" + str(current_datetime)+"/"
    
    if not os.path.isdir(WORK_FOLDER):
        os.mkdir(WORK_FOLDER)
    
    if premaps==None:
        sota_delay = 2
        number_runs = 1
        for n in range(number_runs):
            RUN_DIR = WORK_FOLDER +"run_" + f"{n:03}" + "/"
            os.mkdir(RUN_DIR)
            base_mapping = generateApps()
            run_simple_dvfs_after_delay(base_mapping, delay = sota_delay, workdir = RUN_DIR)
    else:
        sota_delay = 2
        for m in range(len(premaps)):
            RUN_DIR = WORK_FOLDER +"run_" + f"{m:03}" + "/"
            os.mkdir(RUN_DIR)
            print("**********SOTA Run: " + str(m) + "*********************")
            run_simple_dvfs_after_delay(premaps[m], delay = sota_delay, workdir = RUN_DIR)



def eval_run_baseline(premaps=None):
    global mon
    mon = Monitor("auto", refresh_rate= 1, logging=True, workdir="./results/")
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    WORK_FOLDER = RESULTS_FOLDER + "baseline_" + str(current_datetime)+"/"
    
    if not os.path.isdir(WORK_FOLDER):
        os.mkdir(WORK_FOLDER)
    if premaps == None:
        number_runs = 1
        for n in range(number_runs):
            RUN_DIR = WORK_FOLDER +"run_" + f"{n:03}" + "/"
            os.mkdir(RUN_DIR)
            base_mapping = generateApps()
            run_simple(base_mapping, workdir = RUN_DIR)
    else:
        exefile = open(WORK_FOLDER+"time.log", "w")
        for m in range(len(premaps)):
            RUN_DIR = WORK_FOLDER +"run_" + f"{m:03}" + "/"
            os.mkdir(RUN_DIR)
            #exefile = open(RUN_DIR+"time.log", "w")
            print("**********Baseline Run: " + str(m) + "*********************")
            time_ = run_simple(premaps[m], workdir = RUN_DIR)
            exefile.write(str(time_) + "\n")
        exefile.close()


def eval_run_policy(policy, premaps= None):
    global mon
    mon = Monitor("auto", refresh_rate= 1, logging=True, workdir="./results/") #refresh was 0.5
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    WORK_FOLDER = RESULTS_FOLDER + policy.name.lower() +"_" + str(current_datetime)+"/"
    global exefile
    
    if not os.path.isdir(WORK_FOLDER):
        os.mkdir(WORK_FOLDER)
    if premaps == None:
        sota_delay = 2
        number_runs = 1
        for n in range(number_runs):
            RUN_DIR = WORK_FOLDER +"run_" + f"{n:03}" + "/"
            os.mkdir(RUN_DIR)
            exefile = open(RUN_DIR+"time.log", "w")
            base_mapping = generateApps()
            time_ = run_with_policy(base_mapping,  delay = sota_delay, Policy=policy, workdir = RUN_DIR)
            exefile.write(str(time_) + "\n")
            exefile.close()
    else:
        sota_delay = 2
        exefile = open(WORK_FOLDER+"time.log", "w")
        for m in range(len(premaps)):
            RUN_DIR = WORK_FOLDER +"run_" + f"{m:03}" + "/"
            os.mkdir(RUN_DIR)
            print("**********" + policy.name + "Run: " + str(m) + "*********************")
            time_ = run_with_policy(premaps[m],  delay = sota_delay, Policy=policy, workdir = RUN_DIR)
            exefile.write(str(time_) + "\n")
        exefile.close()


def fixedCoreProxy(curr_map):
    index = -1
    for idx  in range(len(curr_map)):
        if "tcc" in curr_map[idx]:
            index = idx
    tmp_map = list(curr_map)
    moving_app = curr_map[1]
    tmp_map[index] = moving_app
    tmp_map[1] = './tcc'
    return tmp_map

    
if __name__ == "__main__":
    startClean()
    restoreFreqs()
    #eval_eval_run_sota()
    #eval_run_baseline()
    #run_training() 
    #run_motiv()
    num_maps = 100
    premaps = []
    # mappfile=open("results/maps.txt", "w")
    # for x in range(num_maps):
    #     premaps.append(generateApps())
    # mappfile.write(str(premaps))
    # mappfile.close()
    premaps = [['spec-zeusmp', 'spec-astar', 'spec-povray', 'spec-lbm', 'spec-omnetpp', './tcc'], ['spec-bzip2', 'spec-leslie3d', 'spec-bwaves', 'spec-h264ref', 'spec-gromacs', './tcc'], ['spec-leslie3d', 'spec-cactusADM', 'spec-povray', 'spec-zeusmp', './tcc', 'spec-hmmer'], ['./tcc', 'spec-bzip2', 'spec-omnetpp', 'spec-hmmer', 'spec-gcc', 'spec-lbm'], ['spec-h264ref', 'spec-cactusADM', './tcc', 'spec-omnetpp', 'spec-bwaves', 'spec-gobmk'], ['./tcc', 'spec-astar', 'spec-milc', 'spec-gromacs', 'spec-lbm', 'spec-sphinx3'], ['spec-hmmer', 'spec-bwaves', './tcc', 'spec-leslie3d', 'spec-h264ref', 'spec-omnetpp'], ['spec-gobmk', 'spec-gromacs', 'spec-lbm', 'spec-omnetpp', './tcc', 'spec-gcc'], ['spec-bwaves', 'spec-namd', 'spec-bzip2', './tcc', 'spec-gromacs', 'spec-sphinx3'], ['spec-gobmk', 'spec-h264ref', './tcc', 'spec-namd', 'spec-astar', 'spec-lbm'], ['spec-gromacs', './tcc', 'spec-gobmk', 'spec-cactusADM', 'spec-lbm', 'spec-milc'], ['spec-zeusmp', 'spec-sphinx3', './tcc', 'spec-bzip2', 'spec-gobmk', 'spec-gcc'], ['spec-leslie3d', 'spec-cactusADM', 'spec-namd', './tcc', 'spec-gromacs', 'spec-omnetpp'], ['./tcc', 'spec-zeusmp', 'spec-astar', 'spec-leslie3d', 'spec-bzip2', 'spec-povray'], ['spec-gromacs', 'spec-leslie3d', './tcc', 'spec-gcc', 'spec-hmmer', 'spec-bzip2'], ['spec-leslie3d', 'spec-povray', 'spec-gromacs', 'spec-namd', 'spec-astar', './tcc'], ['spec-zeusmp', 'spec-omnetpp', './tcc', 'spec-lbm', 'spec-gcc', 'spec-namd'], ['spec-povray', 'spec-h264ref', 'spec-hmmer', 'spec-sphinx3', 'spec-leslie3d', './tcc'], ['spec-namd', './tcc', 'spec-povray', 'spec-gobmk', 'spec-gcc', 'spec-hmmer'], ['spec-bzip2', 'spec-omnetpp', 'spec-povray', 'spec-lbm', './tcc', 'spec-cactusADM'], ['spec-mcf', 'spec-bzip2', 'spec-hmmer', './tcc', 'spec-gromacs', 'spec-cactusADM'], ['spec-mcf', './tcc', 'spec-gromacs', 'spec-cactusADM', 'spec-gcc', 'spec-bwaves'], ['spec-namd', 'spec-astar', 'spec-lbm', 'spec-leslie3d', './tcc', 'spec-hmmer'], ['spec-h264ref', 'spec-povray', './tcc', 'spec-astar', 'spec-gobmk', 'spec-bwaves'], ['./tcc', 'spec-milc', 'spec-zeusmp', 'spec-omnetpp', 'spec-astar', 'spec-namd'], ['spec-namd', 'spec-astar', 'spec-milc', 'spec-h264ref', './tcc', 'spec-leslie3d'], ['spec-bwaves', 'spec-sphinx3', 'spec-cactusADM', 'spec-hmmer', './tcc', 'spec-h264ref'], ['spec-h264ref', 'spec-mcf', 'spec-namd', 'spec-gcc', './tcc', 'spec-lbm'], ['spec-hmmer', 'spec-cactusADM', 'spec-astar', 'spec-leslie3d', './tcc', 'spec-gromacs'], ['spec-namd', 'spec-gcc', 'spec-milc', './tcc', 'spec-cactusADM', 'spec-lbm'], ['spec-povray', 'spec-milc', './tcc', 'spec-gcc', 'spec-astar', 'spec-gromacs'], ['spec-leslie3d', 'spec-h264ref', './tcc', 'spec-sphinx3', 'spec-zeusmp', 'spec-omnetpp'], ['./tcc', 'spec-povray', 'spec-hmmer', 'spec-lbm', 'spec-zeusmp', 'spec-astar'], ['spec-namd', './tcc', 'spec-h264ref', 'spec-hmmer', 'spec-bwaves', 'spec-gromacs'], ['./tcc', 'spec-namd', 'spec-hmmer', 'spec-bzip2', 'spec-cactusADM', 'spec-milc'], ['./tcc', 'spec-bzip2', 'spec-h264ref', 'spec-gobmk', 'spec-cactusADM', 'spec-bwaves'], ['spec-zeusmp', 'spec-mcf', 'spec-bzip2', './tcc', 'spec-bwaves', 'spec-leslie3d'], ['spec-omnetpp', './tcc', 'spec-h264ref', 'spec-hmmer', 'spec-milc', 'spec-leslie3d'], ['spec-sphinx3', 'spec-omnetpp', 'spec-milc', './tcc', 'spec-hmmer', 'spec-astar'], ['spec-cactusADM', 'spec-gcc', 'spec-milc', './tcc', 'spec-leslie3d', 'spec-povray'], ['spec-astar', 'spec-milc', 'spec-povray', 'spec-bwaves', './tcc', 'spec-omnetpp'], ['spec-hmmer', 'spec-cactusADM', './tcc', 'spec-lbm', 'spec-bwaves', 'spec-bzip2'], ['spec-gromacs', 'spec-hmmer', 'spec-bzip2', 'spec-lbm', './tcc', 'spec-cactusADM'], ['spec-astar', 'spec-hmmer', 'spec-gcc', './tcc', 'spec-milc', 'spec-omnetpp'], ['spec-omnetpp', './tcc', 'spec-gromacs', 'spec-bwaves', 'spec-namd', 'spec-zeusmp'], ['spec-milc', 'spec-gobmk', 'spec-h264ref', 'spec-cactusADM', 'spec-hmmer', './tcc'], ['spec-gobmk', 'spec-milc', 'spec-bzip2', 'spec-sphinx3', 'spec-lbm', './tcc'], ['spec-hmmer', 'spec-namd', 'spec-milc', 'spec-gcc', 'spec-h264ref', './tcc'], ['spec-sphinx3', 'spec-omnetpp', './tcc', 'spec-bwaves', 'spec-lbm', 'spec-h264ref'], ['spec-omnetpp', 'spec-povray', 'spec-bzip2', './tcc', 'spec-milc', 'spec-mcf'], ['spec-mcf', 'spec-bwaves', 'spec-povray', 'spec-astar', 'spec-gromacs', './tcc'], ['spec-sphinx3', 'spec-namd', 'spec-h264ref', 'spec-bwaves', 'spec-milc', './tcc'], ['spec-namd', 'spec-bzip2', 'spec-zeusmp', 'spec-h264ref', 'spec-povray', './tcc'], ['spec-bwaves', 'spec-povray', './tcc', 'spec-mcf', 'spec-sphinx3', 'spec-gobmk'], ['./tcc', 'spec-gcc', 'spec-milc', 'spec-povray', 'spec-mcf', 'spec-namd'], ['spec-sphinx3', 'spec-gcc', './tcc', 'spec-bwaves', 'spec-lbm', 'spec-zeusmp'], ['./tcc', 'spec-namd', 'spec-gromacs', 'spec-mcf', 'spec-gobmk', 'spec-sphinx3'], ['spec-milc', 'spec-gobmk', 'spec-zeusmp', './tcc', 'spec-cactusADM', 'spec-hmmer'], ['./tcc', 'spec-omnetpp', 'spec-hmmer', 'spec-gromacs', 'spec-h264ref', 'spec-milc'], ['spec-gobmk', 'spec-bwaves', 'spec-zeusmp', './tcc', 'spec-gcc', 'spec-gromacs'], ['spec-gromacs', 'spec-gobmk', 'spec-zeusmp', 'spec-cactusADM', 'spec-namd', './tcc'], ['spec-h264ref', 'spec-sphinx3', 'spec-zeusmp', 'spec-lbm', './tcc', 'spec-astar'], ['spec-povray', 'spec-cactusADM', 'spec-sphinx3', 'spec-omnetpp', './tcc', 'spec-gobmk'], ['spec-hmmer', 'spec-gobmk', 'spec-mcf', 'spec-astar', './tcc', 'spec-namd'], ['spec-gcc', 'spec-leslie3d', 'spec-namd', 'spec-sphinx3', 'spec-mcf', './tcc'], ['spec-omnetpp', 'spec-milc', './tcc', 'spec-cactusADM', 'spec-sphinx3', 'spec-mcf'], ['spec-omnetpp', './tcc', 'spec-sphinx3', 'spec-leslie3d', 'spec-zeusmp', 'spec-bzip2'], ['spec-omnetpp', 'spec-bzip2', 'spec-bwaves', 'spec-hmmer', './tcc', 'spec-leslie3d'], ['spec-h264ref', 'spec-gcc', 'spec-bzip2', 'spec-omnetpp', './tcc', 'spec-povray'], ['spec-sphinx3', 'spec-milc', 'spec-zeusmp', './tcc', 'spec-mcf', 'spec-astar'], ['spec-astar', 'spec-gobmk', 'spec-gromacs', './tcc', 'spec-lbm', 'spec-bzip2'], ['spec-hmmer', './tcc', 'spec-sphinx3', 'spec-gromacs', 'spec-omnetpp', 'spec-zeusmp'], ['./tcc', 'spec-gromacs', 'spec-bwaves', 'spec-lbm', 'spec-bzip2', 'spec-zeusmp'], ['./tcc', 'spec-milc', 'spec-leslie3d', 'spec-gobmk', 'spec-hmmer', 'spec-sphinx3'], ['spec-lbm', 'spec-mcf', 'spec-gobmk', 'spec-namd', './tcc', 'spec-sphinx3'], ['spec-zeusmp', 'spec-gromacs', 'spec-lbm', 'spec-mcf', 'spec-bwaves', './tcc'], ['spec-bzip2', './tcc', 'spec-sphinx3', 'spec-povray', 'spec-gcc', 'spec-lbm'], ['spec-zeusmp', 'spec-hmmer', 'spec-gobmk', './tcc', 'spec-leslie3d', 'spec-h264ref'], ['spec-leslie3d', 'spec-milc', 'spec-mcf', 'spec-astar', './tcc', 'spec-cactusADM'], ['spec-gobmk', 'spec-lbm', 'spec-zeusmp', 'spec-cactusADM', './tcc', 'spec-leslie3d'], ['spec-mcf', 'spec-sphinx3', './tcc', 'spec-hmmer', 'spec-namd', 'spec-omnetpp'], ['./tcc', 'spec-gcc', 'spec-bzip2', 'spec-astar', 'spec-gromacs', 'spec-leslie3d'], ['spec-mcf', 'spec-hmmer', 'spec-milc', './tcc', 'spec-bzip2', 'spec-gobmk'], ['./tcc', 'spec-sphinx3', 'spec-cactusADM', 'spec-omnetpp', 'spec-gromacs', 'spec-hmmer'], ['./tcc', 'spec-hmmer', 'spec-lbm', 'spec-omnetpp', 'spec-povray', 'spec-gcc'], ['spec-gcc', 'spec-milc', 'spec-omnetpp', 'spec-h264ref', 'spec-cactusADM', './tcc'], ['spec-bwaves', 'spec-gcc', './tcc', 'spec-namd', 'spec-h264ref', 'spec-hmmer'], ['spec-namd', 'spec-sphinx3', 'spec-astar', './tcc', 'spec-bwaves', 'spec-hmmer'], ['./tcc', 'spec-lbm', 'spec-povray', 'spec-cactusADM', 'spec-namd', 'spec-astar'], ['./tcc', 'spec-lbm', 'spec-bzip2', 'spec-cactusADM', 'spec-gromacs', 'spec-astar'], ['spec-namd', 'spec-lbm', 'spec-zeusmp', './tcc', 'spec-gromacs', 'spec-astar'], ['spec-namd', 'spec-astar', './tcc', 'spec-cactusADM', 'spec-mcf', 'spec-omnetpp'], ['spec-omnetpp', 'spec-sphinx3', 'spec-gobmk', 'spec-cactusADM', 'spec-h264ref', './tcc'], ['spec-omnetpp', 'spec-lbm', './tcc', 'spec-mcf', 'spec-zeusmp', 'spec-hmmer'], ['spec-lbm', 'spec-bzip2', 'spec-namd', 'spec-gobmk', 'spec-omnetpp', './tcc'], ['spec-namd', 'spec-omnetpp', 'spec-cactusADM', 'spec-gcc', './tcc', 'spec-povray'], ['spec-gromacs', './tcc', 'spec-leslie3d', 'spec-mcf', 'spec-sphinx3', 'spec-hmmer'], ['spec-lbm', 'spec-cactusADM', 'spec-namd', 'spec-h264ref', './tcc', 'spec-gobmk'], ['spec-mcf', 'spec-bzip2', 'spec-omnetpp', 'spec-hmmer', 'spec-leslie3d', './tcc'], ['./tcc', 'spec-povray', 'spec-zeusmp', 'spec-gromacs', 'spec-astar', 'spec-gobmk']]
    # eval_run_baseline(premaps)
    # print("Finished baselines *************")
    # pol1 = DVFS()
    # eval_run_policy(policy=pol1, premaps=premaps)
    # print("Finished sota *****************")
    # pol2 = FixedCoreDenver()
    # eval_run_policy(policy=pol2, premaps=premaps)
    # print("Finished  Fixed *****************")
    # pol3 = NeuralNet()
    # eval_run_policy(policy=pol3, premaps=premaps)
    pol4 = FixedCoreARM()
    eval_run_policy(policy=pol4, premaps=premaps)
    



