#!/bin/bash
file=$1

cat energy.txt | grep Joules | awk '{print $1;}' >> $1
