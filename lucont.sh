SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
perf stat -B -ecycles:u,instructions:u -o lucont.ipc taskset -c $1 $SPLASH_DIR/kernels/lu/contiguous_blocks/LU -p1 -n2048 >> lucont.out