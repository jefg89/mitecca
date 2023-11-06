SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
#perf stat -B -ecycles:u,instructions:u -o cholesky.ipc 
taskset -c $1 $SPLASH_DIR/kernels/cholesky/CHOLESKY -p1 < $SPLASH_DIR/kernels/cholesky/inputs/tk29.O >> cholesky.out