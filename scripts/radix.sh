SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
taskset -c $1 $SPLASH_DIR/kernels/radix/RADIX -p1 -n9048576 >> radix.out