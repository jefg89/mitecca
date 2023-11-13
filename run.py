from config import *
from monitor import *
from retthreading import *
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


available_apps = ['spec-gcc', 'spec-milc', 'spec-bzip2', 'spec-sphinx3', 'spec-astar', 'spec-lbm',
                  'spec-bwaves', 'spec-mcf', 'spec-zeusmp',  'spec-namd', 'spec-h264ref', 'spec-gobmk',
                  'splash-barnes', 'splash-cholesky', 'splash-lu', 'splash-ocean', 'splash-radix', 'splash-raytrace',
                  'splash-fmm']
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
    print("[Migration:] Moving apps to follow new mapping:")
    print(newmap)
    tmp_pids = list(pids)
    #Only apply migration if the new candidate is different than current mapping
    if (newmap != mapping):
        #check each app for it's new core
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
        mapping = newmap
    return tmp_pids  


def saveTraces(of, original_map, before_mig, dvfs):
    if (before_mig):    
        if (dvfs):
            of.write("1\t")
        else:
            of.write("0\t")
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
    killProc("dvfs.sh")
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

    #***************************************
    # Apply the policy here
    migration = Policy.executePolicy(mapping)
    #
    # **************************************


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

    saveTraces(of, base_map, before_mig=True, dvfs=False)
    
    #apply dvfs
    for c in range(len(migration)):
        if "tcc" in migration[c]:
            attack_core = c
    applyDVFS(attack_core)
    log_file.write("[DVFS]: Applying DVFS to core " + str(attack_core) + "\n")


    #then migrate
    log_file.write("[Migration:] Moving apps to follow new mapping:" + str(migration) + "\n")
    pids = executeMigration(migration, pids)
    #and start recording again
    mon.record()
    print(pids)
    while not mon.isdone():
        time.sleep(0.01)

    saveTraces(of, base_map, before_mig=False, dvfs=True)

    #umm let's do it again at least of couple of times
    #but do not apply dvfs, since we are doing so already
  
    for times in range(7):
        #first generate random variant
        migration = generateVariant(mapping)
        #trigger recording
        mon.record()
        #wait a little for the the trace to be recorded
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=True, dvfs=True)
        #then migrate
        log_file.write("[Migration:] Moving apps to follow new mapping:" + str(migration) + "\n")
        pids = executeMigration(migration, pids)
        #and start recording again
        mon.record()
        print(pids)
        while not mon.isdone():
            time.sleep(0.01)
        #save it 
        saveTraces(of, base_map, before_mig=False, dvfs=True)

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
    
    num_bases = 50
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
    mon = Monitor("auto", refresh_rate= 0.5, logging=True, workdir="./results/")
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
    mon = Monitor("auto", refresh_rate= 0.5, logging=True, workdir="./results/")
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
        for m in range(len(premaps)):
            RUN_DIR = WORK_FOLDER +"run_" + f"{m:03}" + "/"
            os.mkdir(RUN_DIR)
            print("**********Baseline Run: " + str(m) + "*********************")
            run_simple(premaps[m], workdir = RUN_DIR)


def eval_run_policy(policy, premaps= None):
    global mon
    mon = Monitor("auto", refresh_rate= 0.5, logging=True, workdir="./results/")
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    WORK_FOLDER = RESULTS_FOLDER + policy.name.lower() +"_" + str(current_datetime)+"/"
    
    
    if not os.path.isdir(WORK_FOLDER):
        os.mkdir(WORK_FOLDER)
    if premaps == None:
        sota_delay = 2
        number_runs = 1
        for n in range(number_runs):
            RUN_DIR = WORK_FOLDER +"run_" + f"{n:03}" + "/"
            os.mkdir(RUN_DIR)
            base_mapping = generateApps()
            run_with_policy(base_mapping,  delay = sota_delay, Policy=policy, workdir = RUN_DIR)
    else:
        sota_delay = 2
        for m in range(len(premaps)):
            RUN_DIR = WORK_FOLDER +"run_" + f"{m:03}" + "/"
            os.mkdir(RUN_DIR)
            print("**********" + policy.name + "Run: " + str(m) + "*********************")
            run_with_policy(premaps[m],  delay = sota_delay, Policy=policy, workdir = RUN_DIR)



    
if __name__ == "__main__":
    startClean()
    restoreFreqs()
    #eval_eval_run_sota()
    #eval_run_baseline()
    #run_training() 
    #run_motiv()

    premaps = []
    # mappfile=open("maps.txt", "w")
    # for x in range(100):
    #     premaps.append(generateApps())
    # mappfile.write(str(premaps))
    # mappfile.close()
    premaps.append(['spec-milc', 'spec-namd', 'spec-mcf', './tcc', 'spec-astar', 'splash-cholesky'])

    # eval_run_baseline(premaps)
    # print("Finished baselines *************")
   
    # print(premaps[0].index("splash-cholesky"))

    # bench = 'splash-'
    # p_prox =  'CHOLESKY'

    # idx = premaps[0].index(bench + p_prox.lower())

    # print(idx)

   
    pol1 = DVFS()
    eval_run_policy(policy=pol1, premaps=premaps)
    print("Finished sota *****************")
    pol = FixedCoreDenver()
    eval_run_policy(policy=pol, premaps=premaps)
    



