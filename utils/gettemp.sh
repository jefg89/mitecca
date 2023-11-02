#!/bin/bash
TFILE=/sys/class/thermal/thermal_zone$1/temp
out=temp.out

rm -rf temp.out
echo "Getting temperature samples..."
while true
do

	while IFS= read -r line
 	do
	 	temp=$line
	 	echo $temp >>$out
	done < $TFILE
	sleep 0.01
done
