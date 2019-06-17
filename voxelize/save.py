
import csv 
from stltovoxel import doExport 
import numpy as np



l=[]
n=doExport('/home/user/stl-to-voxel-master/cube.stl',98)
for i in range(n.shape[0]):
    for j in range(n.shape[1]):
        for k in range(n.shape[2]):
            l.append(n[i][j][k])
with open('data.csv', 'a') as f:
    writer = csv.writer(f)
    writer.writerow(l)
