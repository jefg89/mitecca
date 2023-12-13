from itertools import combinations

arm_cores = [0, 3, 4, 5]
denver_cores = [1, 2]

def getAverage(array):
    sum = 0
    for i in range(len(array)):
        sum += array[i]
    return sum / len(array)


class Policy:
    def __init__(self, base_map=None):
        self._bmap = base_map

    def printMap(self):
        print(self._bmap)
#DVFS policy (sota)
#does not change mapping
class DVFS(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name ="DVFS"
    
    def executePolicy(self, curr_map, original_map=None, curr_dvfs = None, current_features=None, 
                      current_efficiency=None, attack_core=None):
        return curr_map, 0

#Naive: always move to first denver core (1)
class FixedCoreDenver(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name = "FixedCore"
    
    def executePolicy(self, curr_map, original_map=None, curr_dvfs = None, current_features=None, 
                      current_efficiency=None, attack_core=None):
        index = -1
        for idx  in range(len(curr_map)):
            if "tcc" in curr_map[idx]:
                index = idx
        tmp_map = list(curr_map)
        moving_app = curr_map[1]
        tmp_map[index] = moving_app
        tmp_map[1] = './tcc'
        return tmp_map, 0

#Naive: always move to first arm core (5)
class FixedCoreARM(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name = "FixedCoreARM"
    
    def executePolicy(self, curr_map, original_map=None, curr_dvfs = None, current_features=None, 
                      current_efficiency=None, attack_core=None):
        index = -1
        for idx  in range(len(curr_map)):
            if "tcc" in curr_map[idx]:
                index = idx
        tmp_map = list(curr_map)
        moving_app = curr_map[5]
        tmp_map[index] = moving_app
        tmp_map[5] = './tcc'
        return tmp_map, 0

#Heuristic: Least Performing Cluster Most Performing Core (LPCMPC)
class LPCMPCore(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name = "lpcmpcore"
    
    def executePolicy(self, curr_map, original_map=None, curr_dvfs = None, current_features=None, 
                      current_efficiency=None, attack_core=None):
        attack_index = -1
        for idx  in range(len(curr_map)):
            if "tcc" in curr_map[idx]:
                attack_index = idx

        dever_ipcs = []
        arm_ipcs = []
        #Let's find the least performing cluster
        for core in denver_cores:
            dever_ipcs.append(current_features[core*3])
        for core in arm_cores:
            arm_ipcs.append(current_features[core*3])
        
        cluster_candidate = list(denver_cores)
        if getAverage(dever_ipcs) > getAverage(arm_ipcs):
            cluster_candidate = list(arm_cores)

        
        #Now the most performing core from that cluster
        max = 0
        for core in cluster_candidate:
            if current_features[core*3] > max:
                max = current_features[core*3]
                core_idx = core
        
        #and switch
        tmp_map = list(curr_map)
        moving_app = curr_map[core_idx]
        tmp_map[attack_index] = moving_app
        tmp_map[core_idx] = './tcc'
        return tmp_map, 0










# base_map = ['spec-mcf', 'spec-bzip2', 'spec-milc', 'spec-bwaves', './tcc', 'spec-astar']
# features = [4,0,0, #arm
#             2,0,0,
#             3,0,0,
#             2,0,0,#arm
#             0,0,0,#arm
#             1,0,0] #arm

# policy = LPCMPCore()
# new_map, eff = policy.executePolicy(base_map, original_map=None, curr_dvfs = None, current_features=features, 
#                       current_efficiency=None, attack_core=None)
# print(new_map)
# print(policy.name)





