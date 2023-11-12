import sys
#print("Power (W) \t Makespan (s) \t Energy (J)")
time = float (sys.argv[1])
f = open("power.out", "r")
pows = f.readlines()
sum = 0
for p in pows:
    sum+=float(p)
avg = sum/(1000*len(pows))
print( str(avg) + "\t" + str(time) + "\t" + str(avg * time) )


