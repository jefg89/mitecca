SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
#perf stat -B -ecycles:u,instructions:u -o raytrace.ipc 
taskset -c $1 $SPLASH_DIR/apps/raytrace/RAYTRACE -p1 -m64 $SPLASH_DIR/apps/raytrace/inputs/balls4.env >> raytrace.out