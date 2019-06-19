from flask import Flask, render_template, request ,session, redirect , url_for
import os
import csv
import time
import re
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
import base64
from io import BytesIO
import stl
import math
import numpy as np
from sklearn import preprocessing
from stl import mesh
from mpl_toolkits import mplot3d
from voxelize.stltovoxel import doExport
from voxelize import *
from utils import *

#this function is responsible for the rotation  of a 3d matrix around a givin axis and a given angle.
#it takes as an input the axis of rotation the angle of rotation and the matrix to rotate
#output is a rotated 3D matrix

def rot(X, theta, axis):
  #'''Rotate multidimensional array `X` `theta` degrees around axis `axis`'''
    pi=np.pi
    theta=pi*theta/180
    c, s = np.cos(theta), np.sin(theta)
    if axis == 'x':
        return np.dot(np.array([[1.,  0,  0],[0 ,  c, s],[0 ,  -s,  c]]),X)
    elif axis == 'y': return np.dot( np.array([
    [c,  0,  -s],
    [0,  1,   0],
    [s,  0,   c]
  ]),X)
    elif axis == 'z': return np.dot( np.array([
    [c, s,  0 ],
    [-s,  c,  0 ],
    [0,  0,  1.],
  ]),X)



#This function is the one responcible for plotting the 3d object
#the plot is a 3D view of the object along with 3 other 2D plots of
#the projection of the object respectively on XY, XZ and YZ
#input is a mesh, center of mass, principle rotation axes of the part and the maximum Length
# output is an image of the plots presenting the object

def show(your_mesh,cog,inertia,l):
    fig = plt.figure(figsize=(10,10))
    axes = fig.add_subplot(7,6,(1,24), projection='3d')
    axes.title.set_text('3D plot')
# plot the cordinate system of the part
    v1= inertia[0]
    v2= inertia[1]
    v3= inertia[2]
    X,Y,Z = zip(cog, cog,cog)
    U,V,W = zip(v1,v2,v3)
    axes.quiver(X,Y,Z,U,V,W, length=l+1, arrow_length_ratio=0.1, color=['r','g','b'])

  #change the trancperacy of the part to be able to see its COG and axes
    face=mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
    face.set_facecolor((0,0,1,0.3))
    axes.add_collection3d(face)
    axes.scatter(cog[0],cog[1],cog[2],color='black')

 # Auto scale to the mesh size and lable the axes
    scale = your_mesh.points.flatten(1)
    axes.auto_scale_xyz(scale, scale, scale)
    axes.set_xlabel('x')
    axes.set_ylabel('Y')
    axes.set_zlabel('z')

    #these two images discribe the feeding direction and the gravity
    #when changing the location of the project make sure to change the path name
    im = plt.imread(get_sample_data('/home/user/DFF/static/feedd.png'))
    im2 = plt.imread(get_sample_data("/home/user/DFF/static/gravity.png"))

    #this code places the two images above in their proper positions in the output image
    newax = fig.add_axes([0.4, 0.8, 0.2, 0.2], anchor='NE', zorder=-1)
    newax.imshow(im)
    newax.axis('off')

    newax = fig.add_axes([0, 0.5, 0.2, 0.2])
    newax.imshow(im2)
    newax.axis('off')


#these lines of codes down below are going to create the projection of the 3D object on three different plans
# XY, XZ and  YZ
    #XY
    face=mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
    face.set_facecolor((0,0,1,0.3))
    axes=fig.add_subplot(7,6,(25,38) , projection='3d')
    axes.title.set_text('X-Y')
    axes.view_init(azim=0, elev=90)
    axes.add_collection3d(face)
    scale = your_mesh.points.flatten(1)
    axes.auto_scale_xyz(scale, scale, scale)
    axes.set_xlabel('x')
    axes.set_ylabel('Y')
    axes.set_zticks([])

    #XZ
    face=mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
    face.set_facecolor((0,0,1,0.3))
    axes=fig.add_subplot(7,6,(27,40), projection='3d')
    axes.view_init(azim=-90, elev=0)
    axes.title.set_text('X-Z')
    axes.add_collection3d(face)
    scale = your_mesh.points.flatten(1)
    axes.auto_scale_xyz(scale, scale, scale)
    axes.set_xlabel('x')
    axes.set_zlabel('z')
    plt.yticks([])

    #YZ
    face=mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
    face.set_facecolor((0,0,1,0.3))
    axes=fig.add_subplot(7,6,(29,42), projection='3d')
    axes.view_init(azim=0, elev=0)
    axes.title.set_text('Y-Z')
    axes.add_collection3d(face)
    scale =your_mesh.points.flatten(1)
    axes.auto_scale_xyz(scale, scale, scale)
    axes.set_ylabel('Y')
    axes.set_zlabel('z')
    plt.xticks([])



    #encode the mesh to be able to display it on the web
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png')
    return base64.b64encode(tmpfile.getvalue())

#this function takes as an input a matrix and tests if it is positive or negative
def is_pos(x):
    return np.all(np.linalg.eigvals(x) > 0)

#This function calculates the number of vertices that has negative x coordinate and the positive onesself.
#the function makes sure that the number of positive vertices is always bigger.
def to_original(mesh):
    m=mesh.points
    v0=m[:,0]
    v1=m[:,3]
    v2=m[:,6]
    neg=0
    pos=0
    for i in range(m.shape[0]):
        if v0[i]>0:
            pos+=1
        else: neg +=1
        if v1[i]>=0:
            pos+1
        else: neg +=1
        if v2[i]>0:
            pos+=1
        else: neg +=1
    print(pos, neg )
    if pos < neg:
        print('done')
        mesh.rotate([0,1,0], math.radians(180))

#this function tests if the moment of inertia is diagonal or notself.
#if not it rotates the mesh to make the moment of inertia diagonal
def align(mesh, ax, inertia):
    m=mesh.points
    bx=np.linalg.inv(ax)
    v0=m[:,0:3]
    v1=m[:,3:6]
    v2=m[:,6:9]
    if np.count_nonzero(inertia - np.diag(np.diagonal(inertia)))!= 0:
        print('done')
        for i in range(m.shape[0]):
            m[i,0:3] = bx.dot(v0[i])
            m[i,3:6] = bx.dot(v1[i])
            m[i,6:9] = bx.dot(v2[i])
            mesh.points=m
    return mesh

# this function takes a mesh calculates her principle axes hef rotation and transfer it to the cartesian coordinate system
def correct(mesh):
    volume, cog, inertia = mesh.get_mass_properties()
    eigs, ax = np.linalg.eigh(inertia)
    angleX = np.arccos(np.dot([1, 0, 0],np.around(ax[0,:])) /  ( np.linalg.norm([1, 0, 0])*np.linalg.norm(np.around(ax[0,:]))))
    angleY = np.arccos(np.dot([0, 1, 0],np.around(ax[1,:])) / ( np.linalg.norm([0, 1, 0]) *np.linalg.norm(np.around(ax[1,:]))))
    angleZ = np.arccos(np.dot([0, 0, 1],np.around(ax[2,:])) / ( np.linalg.norm([0, 0, 1]) * np.linalg.norm(np.around(ax[2,:]))))
    print (angleX* 180/np.pi ,'    ', angleY* 180/np.pi  ,'    ',angleZ* 180/np.pi)
    if angleZ==0.0 and angleX==0 and angleY==0.0:
        print('nothing to do')
        return mesh
    elif angleX==0.0 :
        mesh.rotate([1,0,0], angleZ)
        print('rotate X')
        return mesh
    elif angleY==0.0 :
        mesh.rotate([0,1,0], angleX)
        print('rotate Y')
        return mesh
    elif angleZ==0.0 :
        mesh.rotate([0,0,1],angleY)
        print('rotate Z')
        return mesh
    else:
        mesh.rotate([1,0,0],(angleZ))
        return correct(mesh)



#This function has a job of taking an stl file shift it to his center of mass and shift to his main axes
#and make it possible to visualize the part on the web by calling the show() function
#input is an stl file
#output is a encoded image of a corrected 3D object
def convert(file,l):


    your_mesh = mesh.Mesh.from_file(file)



# Load the STL files and add the vectors to the plot
    volume, cog, inertia = your_mesh.get_mass_properties()
    cog = cog.astype(type('float', (float,), {}))
    your_mesh.translate(-cog)
    volume, cog, inertia = your_mesh.get_mass_properties()
    eigs, ax = np.linalg.eigh(inertia)
    m=your_mesh.points

    your_mesh=align(your_mesh, ax, inertia)
    volume, cog, inertia = your_mesh.get_mass_properties()
    eigs, ax = np.linalg.eigh(inertia)
    if is_pos(inertia)== False:
        your_mesh=align(your_mesh,ax, inertia)

    your_mesh=correct(your_mesh)
    to_original(your_mesh)
    cog = cog.astype(type('float', (float,), {}))

    encoded=show(your_mesh,cog,[[1,0,0],[0,1,0],[0,0,1]],l)

    your_mesh.save(file)

    return encoded


#this function is the one responcible for the rotation of the object oround the chosen angles and axes by the user
#it has as input the values of the rotation angles the file name and time of operation so that the rotated object could be saved and called once needed
def rotation(filename,add,x,y,z,l,axx):


    exists = os.path.isfile('uploads/rot_'+add+filename)
    if exists:
        your_mesh = mesh.Mesh.from_file('uploads/rot_'+add+filename)
    else:
        your_mesh = mesh.Mesh.from_file('uploads/'+filename)



  #rotate the part as asked
    x = float(x)
    y= float(y)
    z= float(z)
    volume, cog, inertia = your_mesh.get_mass_properties()
      # transform information to float type
    cog = cog.astype(type('float', (float,), {}))
    if x != 0:
        your_mesh.rotate([1,0,0], math.radians(-x), point=cog)
        axx = rot(axx,x, 'x')

    if y != 0:
        your_mesh.rotate([0,1,0], math.radians(-y), point=cog)
        axx = rot(axx,y, 'y')
    if z != 0:
        your_mesh.rotate([0,0,1], math.radians(-z), point=cog)
        axx= rot(axx,z, 'z')
    #extract information from the stl file
    v, cog, i = your_mesh.get_mass_properties()
    cog = cog.astype(type('float', (float,), {}))

    encoded = show(your_mesh,cog,axx,l)

    your_mesh.save('uploads/rot_'+add+filename)
    return encoded, axx

#this function has the role of mesuring the dimention of the 3D from_object
#on each axis the function will return the dimention the object takes on axis X, Y and Z
def find_mins_maxs(file):
    obj = mesh.Mesh.from_file(file)
    minx = maxx = miny = maxy = minz = maxz = None
    for p in obj.points:
        # p contains (x, y, z)
        if minx is None:
            minx = p[stl.Dimension.X]
            maxx = p[stl.Dimension.X]
            miny = p[stl.Dimension.Y]
            maxy = p[stl.Dimension.Y]
            minz = p[stl.Dimension.Z]
            maxz = p[stl.Dimension.Z]
        else:
            maxx = max(p[stl.Dimension.X], maxx)
            minx = min(p[stl.Dimension.X], minx)
            maxy = max(p[stl.Dimension.Y], maxy)
            miny = min(p[stl.Dimension.Y], miny)
            maxz = max(p[stl.Dimension.Z], maxz)
            minz = min(p[stl.Dimension.Z], minz)
    return maxx-minx, maxy-miny,  maxz-minz

