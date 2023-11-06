SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
#perf stat -B -ecycles:u,instructions:u -o ocean.ipc 
taskset -c $1 $SPLASH_DIR/apps/ocean/contiguous_partitions/OCEAN -p1 -n1026 >> ocean.out