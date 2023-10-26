SPLASH_DIR=/home/jetson/mitecca/Splash-3/codes
taskset -c $1 $SPLASH_DIR/apps/barnes/BARNES < $SPLASH_DIR/apps/barnes/inputs/n16384-p1 >> barnes.out
