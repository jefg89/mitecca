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
    #echo "launching volrend on core $1"
    #time taskset -c $1 $SPLASH_DIR/apps/volrend/VOLREND 1  $SPLASH_DIR/apps/volrend/inputs/head 2 &
    #echo "launching ocean on core $2"
    #time taskset -c $2 $SPLASH_DIR/apps/ocean/contiguous_partitions/OCEAN -p1 -n1026 &
    #echo "launching lucont on core $1"
    #time taskset -c $1 $SPLASH_DIR/kernels/lu/contiguous_blocks/LU -p1 -n2056 >> runs_lu.out

    time taskset -c $1 $SPLASH_DIR/kernels/cholesky/CHOLESKY -p1 < $SPLASH_DIR/kernels/cholesky/inputs/tk29.O >> runs_cho & # about 0.3 &
    time taskset -c $2 $SPLASH_DIR/apps/fmm/FMM < $SPLASH_DIR/apps/fmm/inputs/input.1.16384 >> runs_fmm  #about 0.9

    elapsed=$(date +"%s.%N - ${start}" | bc)
    #perf stat -o energy.txt --append -a -e "power/energy-pkg/" taskset -c $2 time $SPLASH_DIR/kernels/lu/contiguous_blocks/LU -p1 -n4096 >> runs_lu.out
    echo "finished: getting energy results"
    killall tcc
    sudo killall getpower.sh
    python3 getenergy.py $elapsed >> energy.out  
done

#./utils/fix_energy_file.sh fixed.txt
killall dvfs.sh
sleep 1
echo "restoring freq values"
./utils/setallmax.sh
