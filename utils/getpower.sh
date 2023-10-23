#!/bin/bash
PFILE=/sys/bus/i2c/drivers/ina3221x/0-0041/iio\:device1/in_power1_input
out=power.out

rm -rf power.out
echo "Getting power samples..."
while true
do

	while IFS= read -r line
 	do
	 	power=$line
	 	echo $power >>$out
	done < $PFILE
	sleep 0.01
done
