import random
import sys

vpnum = int(sys.argv[1])
lambd = float(sys.argv[2])
output = 'seq%d-lambd%d.txt'%(vpnum,lambd)

f = open(output,'w')
for i in range(vpnum):
    interval = random.expovariate(lambd)
    f.write(str(interval))
    f.write('\n')
f.close()