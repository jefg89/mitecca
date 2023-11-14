from policies import *

import sklearn
import itertools
import joblib
import numpy as np
from tensorflow.keras.models import load_model
from itertools import combinations

import warnings
warnings.filterwarnings("ignore")


from timeit import default_timer as timer

arm_cores = [0, 3, 4, 5]
denver_cores = [1, 2]
indices_of_features_to_scale = list(range(0,19))
num_apps = 6

def generate_unique_mappings(curr_mapping_ids, arm_cores, denver_cores, num_apps):
    unique_mappings = []
    current_arm_apps = sorted([curr_mapping_ids[i] for i in arm_cores])
    current_denver_apps = sorted([curr_mapping_ids[j] for j in denver_cores])

    for arm_apps in combinations(range(num_apps), len(arm_cores)):
        if sorted(arm_apps) == current_arm_apps:
            continue
        denver_apps = [app for app in range(num_apps) if app not in arm_apps]
        if sorted(denver_apps) == current_denver_apps:
            continue

        mapping = [None] * num_apps
        for i, core in enumerate(arm_cores):
            mapping[core] = arm_apps[i]
        for j, core in enumerate(denver_cores):
            mapping[core] = denver_apps[j]

        unique_mappings.append(tuple(mapping))

    return unique_mappings

def construct_row(dvfs, curr_mapping_ids, current_features, new_mapping, current_efficiency):
    data_row = np.zeros(32)
    data_row[0:18] = current_features
    data_row[18] = current_efficiency / 1e9
    data_row[19] = dvfs
    data_row[20:26] = curr_mapping_ids
    data_row[26:32] = new_mapping
    data_row[0] /= 1e9
    data_row[1] /= 1e7
    data_row[2] /= 1e5
    data_row[3] /= 1e9
    data_row[4] /= 1e7
    data_row[5] /= 1e5
    data_row[6] /= 1e9
    data_row[7] /= 1e7
    data_row[8] /= 1e5
    data_row[9] /= 1e9
    data_row[10] /= 1e7
    data_row[11] /= 1e5
    data_row[12] /= 1e9
    data_row[13] /= 1e7
    data_row[14] /= 1e5
    data_row[15] /= 1e9
    data_row[16] /= 1e7
    data_row[17] /= 1e5
    #print(data_row)
    return data_row

def getMappingFromIds(ids, curr_map, original_map):
    map =[]
    for id in ids:
        if id < 0:
            app = ""
        else:
            app = original_map[id]
        map.append(app)
    return map


def isMissing(app, map):
    for x in range(len(map)):
        if app == map[x]:
            return False
    return True



def insertFirstEmpty(app, map):
    for x in range(len(map)):
        if map[x] == '':
            map[x] = app
            break

 
def fixMap(curr_map, new_map):
    tmp =  list(new_map)
    for x in range(len(curr_map)):
        if isMissing(curr_map[x], tmp):
            insertFirstEmpty(curr_map[x], tmp)
    
    return tmp
            

def getIdsFromMappings(original_map, curr_mapping_ids):
    ids = []
    for x in range(len(curr_mapping_ids)):
        rm = 0
        if "*" in curr_mapping_ids[x]:
            id = original_map.index(curr_mapping_ids[x][:-1])
        else:
            id = original_map.index(curr_mapping_ids[x])
        ids.append(id)
    return ids
    

def getMissingAppsIds(mapping):
    missing = []
    for x in range (len(mapping)):
        if "*" in mapping[x]:
            missing.append(x)
    return missing



class NeuralNet(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name ="NeuralNetwork"
        self.model = load_model('mitecca_512.h5')
        self.scaler = joblib.load('scaler.save')


    def executePolicy(self, curr_map, original_map=None, dvfs=None, current_features=None, 
                      current_efficiency=None):
    
        
        #replace with a function than translates to ids from app names
        curr_mapping_ids = getIdsFromMappings(original_map, curr_map)

        #replace with a function to find which apps are missing
        my_none_apps = []
        my_none_idx = getMissingAppsIds(curr_map)
        for idx in my_none_idx:
            my_none_apps.append(curr_mapping_ids[idx])

        #print("none apps: ", my_none_apps)

        #print("current mapping (ids)", curr_mapping_ids)
        
        #first get all the mappings from  the current one
        all_unique_mappings = generate_unique_mappings(curr_mapping_ids, arm_cores, denver_cores, num_apps)
        unique_final_mappings = []
        for perm in all_unique_mappings:
            perm = list(perm)
            for i, app in enumerate(perm):
                if app in my_none_apps:
                    perm[i] = -1
            unique_final_mappings.append(perm)
        unique_final_mappings.append(curr_mapping_ids)

        unique_set_of_mappings = set(tuple(i) for i in unique_final_mappings)
        # print("current: ", curr_mapping_ids)
        # print("unique: ", unique_set_of_mappings )
       
        
        #print(unique_final_mappings)
        

        max = 0
        best = -1
        for mapping in unique_set_of_mappings:
            
            data_row = construct_row(dvfs, curr_mapping_ids, current_features, mapping, current_efficiency) #divided by 1e8
            #print("\n",data_row)
            #print("New row with mapping: ", mapping)
            scaled_features = self.scaler.transform([data_row[indices_of_features_to_scale]])
            row_scaled = data_row.copy()
            row_scaled[indices_of_features_to_scale] = scaled_features[0]
            reshaped = row_scaled.reshape(1, -1)

            #start = timer()
            #print("\n",row_scaled)
            #https://www.tensorflow.org/api_docs/python/tf/keras/Model?hl=en#predict
            pred = float(self.model. __call__([reshaped])[0])
            if pred > max:
                max = pred
                best = mapping
            #predictions.append(pred)
            #end = timer()
            #print("prediction takes : ", end-start)
        #print("best map id: ", best, "in list form ", list(best))
      
        best_map = getMappingFromIds(list(best), curr_map, original_map)
        #print("Best map from inside: ", best_map)           
        return fixMap(curr_map, best_map)


# print("initialing th policy")
# pol = NeuralNet()

# original_map =   ['splash-radix', 'spec-gcc', 'spec-lbm', 'spec-gobmk', 'spec-mcf', './tcc']
# curr_map = ['splash-radix', 'spec-gobmk', 'spec-mcf', 'spec-gcc*', 'spec-lbm*', './tcc']




# current_features =[813385517, 147779097, 5040967, 13013, 8007, 257, 75438024, 40632611, 986594, 2007482144, 830776678, 11681729, 33600390, 15234409, 741180, 813323388, 397199337, 614489]

# current_efficiency = 2254150593.7612915
# print("===> Given the current efficiency: ", current_efficiency/1e9)
# dvfs = 1 

# print("executing the policy")
# print("original map: ", original_map)
# print("current map: ", curr_map)
# start = timer()
# pred = pol.executePolicy(curr_map, original_map, dvfs, current_features, current_efficiency)
# end = timer()
# print("Best map: ", pred)
# print("total time is", end-start)


