#!/bin/bash

sudo perf stat -B -I 100 -ecycles:u,instructions:u -a -o $1 sleep $2
cat $1| grep "ins" > ipc.out;