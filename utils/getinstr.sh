#!/bin/bash

#$1 window lenght in ms
#$2 output file

perf stat -C 0-5 -e instructions,cache-misses,cache-references -B -A  -o  $2 sleep $1 
