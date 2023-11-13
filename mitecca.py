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

def generate_unique_mappings(current_mapping, arm_cores, denver_cores, num_apps):
    unique_mappings = []
    current_arm_apps = sorted([current_mapping[i] for i in arm_cores])
    current_denver_apps = sorted([current_mapping[j] for j in denver_cores])

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

def construct_row(dvfs, current_mapping, current_features, new_mapping, current_efficiency):
    data_row = np.zeros(32)
    data_row[0:18] = current_features
    data_row[18] = current_efficiency / 1e9
    data_row[19] = dvfs
    data_row[20:26] = current_mapping
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

#TODO: implement this
def idsToMap(ids):
    return ids
#TODO: implement this
def mapsToIds(map):
    return map

class NeuralNet(Policy):
    def __init__(self, base_map=None):
        super().__init__(base_map)
        self.name ="NeuralNetwork"
        self.model = load_model('mitecca_512.h5')
        self.scaler = joblib.load('scaler.save')



    def executePolicy(self, base_map, app_dict=None, dvfs=None, current_features=None, 
                      current_efficiency=None):
        
        #replace with a function to find which apps are missing
        my_none_apps = []
        
        #replace with a function than translates to ids from app names
        current_mapping = mapsToIds(base_map)
        
        #first get all the mappings from  the current one
        all_unique_mappings = generate_unique_mappings(current_mapping, arm_cores, denver_cores, num_apps)
        unique_final_mappings = []
        for perm in all_unique_mappings:
            perm = list(perm)
            for i, app in enumerate(perm):
                if app in my_none_apps:
                    perm[i] = -1
            unique_final_mappings.append(perm)

        unique_set_of_mappings = set(tuple(i) for i in unique_final_mappings)
       
        
        #print(unique_final_mappings)
        
        predictions =[]
        max = 0
        best = -1
        for mapping in unique_set_of_mappings:
            
            data_row = construct_row(dvfs, current_mapping, current_features, mapping, current_efficiency) #divided by 1e8
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
        return idsToMap(best)


print("initialing th policy")
pol = NeuralNet()
current_mapping = [3,2,0,1,4,5]
current_features = [423337366,177314997,5435930,2212295672,871853377,18356755,809465059,487286628,27715060,1224008353,333157686,16508741,317840145,152323920,1287185,987232516,308000083,22870347]
current_efficiency = 1643967834.6175015
print("===> Given the current efficiency: ", current_efficiency/1e9)
dvfs = 1 

print("executing the policy")
start = timer()
pred = pol.executePolicy(current_mapping,None, dvfs, current_features, current_efficiency)
end = timer()
print("Best map: ", pred)
print("total time is", end-start)

