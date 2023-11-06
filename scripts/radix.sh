SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
#perf stat -B -ecycles:u,instructions:u -o radix.ipc 
taskset -c $1 $SPLASH_DIR/kernels/radix/RADIX -p1 -n40048576 >> radix.out
#was -9 instead of -n10