#!/bin/bash
SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
rm -rf *.out *.txt			

if [ $4 -eq 1 ]	
then
    ./dvfs.sh $3 &
fi

for i in {1..10}
do
    echo "launching monitoring"
    sudo ./utils/getpower.sh &
    start="$(date +'%s.%N')"
    echo "launching attack on core $3"
    #taskset -c $3 stress --cpu 1 --io 1 --vm 1 --vm-bytes 1M  --timeout 45s &
    taskset -c $3 ./tcc 1 >> tcc.out &
    #echo "launching barnes on core $1"
    #time taskset -c $1 $SPLASH_DIR/apps/barnes/BARNES < $SPLASH_DIR/apps/barnes/inputs/n16384-p1 >> runs_barnes.out &
    echo "launching lucont on core $2"
    time taskset -c $2 $SPLASH_DIR/kernels/lu/contiguous_blocks/LU -p1 -n2056 >> runs_lu.out
    elapsed=$(date +"%s.%N - ${start}" | bc)
    #perf stat -o energy.txt --append -a -e "power/energy-pkg/" taskset -c $2 time $SPLASH_DIR/kernels/lu/contiguous_blocks/LU -p1 -n4096 >> runs_lu.out
    echo "finished: getting energy results"
    killall tcc
    sudo killall getpower.sh
    python3 getenergy.py $elapsed >> energy.out  
done

#./utils/fix_energy_file.sh fixed.txt
killall dvfs.sh
