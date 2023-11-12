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
    
    def executePolicy(self):
        return self._bmap

#Naive: always move to first denver core (1)
class FixedCoreDenver(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name = "FixedCore"
    
    def executePolicy(self, curr_map):
        index = -1
        for idx  in range(len(curr_map)):
            if "tcc" in curr_map[idx]:
                index = idx
        tmp_map = list(curr_map)
        moving_app = curr_map[1]
        tmp_map[index] = moving_app
        tmp_map[1] = './tcc'
        return tmp_map




# base_map = ['spec-mcf', 'spec-bzip2', 'spec-milc', 'spec-bwaves', './tcc', 'spec-astar']
# policy = FixedCoreDenver()
# new_map = policy.executePolicy(base_map)
# print(new_map)
# print(policy.name)





