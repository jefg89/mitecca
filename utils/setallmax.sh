#!/bin/bash

VF_HI=2035200

for core in {0..5}
do
	echo ${VF_HI} | sudo tee /sys/devices/system/cpu/cpu$core/cpufreq/scaling_max_freq
	echo ${VF_HI} | sudo tee /sys/devices/system/cpu/cpu$core/cpufreq/scaling_min_freq
done


