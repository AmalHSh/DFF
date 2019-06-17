"""
This is a main python script for collecting data from the user. This progam renders
index.html and success.html files.
Author: Abdus Sattar Mia
"""

from flask import Flask, render_template, request ,session, redirect , url_for
from flask_session import Session
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
app = Flask(__name__)
SESSION_TYPE = 'redis'
app.config.from_object(__name__)
Session(app)
UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


c=0


#
@app.route("/")
def index():
    session['remember']=1
    session['choice']=[]
    return render_template("index.html", remember=session['remember'])


# data reloaded
@app.route('/data_reload', methods=['POST', 'GET'])
def data_reload():
    if request.method=='POST':
        session['remember']=2
        f_name=session['filename']
        img = session['image']
        choice=session['choice']
        l=session['dimentions'][0]
        return render_template('index.html', remember=session['remember'],choices=choice,X=l,  Y=session['dimentions'][1],Z=session['dimentions'][2],img=img.decode('utf8'),filename=f_name)


# data aded successefully
@app.route("/data_added", methods=['POST','GET'])
def data_added():
    for i in session:
        print (i)
    if request.method =='POST':
#collect the informations from the form
        part_name = request.form["part_name"]
        rotu_size = request.form["rotu_size"]
        difficulty = request.form["difficulty"]
        pressured_air = request.form["pressured_air"]
        parts = request.form["parts"]
        output_track = request.form["output_track"]
        Hooking_grade = request.form["Hooking_grade"]


        filename=session['filename']
        timestr=session['timestr']
        exists = os.path.isfile('uploads/rot_'+timestr+filename)
        if exists:
            file='rot_'+timestr+filename
        else:
            file=filename
        x=session['X']
        y=session['Y']
        z=session['z']
        #creating a line of data to add to the CSV file
        fields=[part_name,rotu_size,Hooking_grade,difficulty,pressured_air,parts,output_track,x,y,z,filename,file]
        session['choice']=fields
        with open(r'data.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
            session['remember']=1
        global c
        c=c+1

    if c%100==0:
        return render_template('congrats.html')
    else:
        return render_template('index.html',comment="Data added succcessefuly!", remember=session['remember'],choices=fields)

#display a .GIF  image to help the admin celebrate each 100 submission
@app.route('/congrats', methods=['POST','GET'])
def congrats():

    choice=session['choice']
    return render_template('index.html',comment="Data added succcessefuly!", remember=session['remember'],choices=choice)


@app.route('/upload', methods=['POST','GET'])
def upload():
    if request.method =='POST':
        #take uploaded file name and save it in the upload directory
        file = request.files['image']
        f_name = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))

        #Calculate object dimentions and save them into a session
        l,w,h=find_mins_maxs('uploads/'+ f_name)
        l = l.astype(type('float', (float,), {}))
        w = w.astype(type('float', (float,), {}))
        h = h.astype(type('float', (float,), {}))
        l=round(l,2)
        w=round(w,2)
        h=round(h,2)
        session['dimentions']=[l,w,h]

        #create time variable to identify the uploaded file and keep track
        timestr = time.strftime("%Y%m%d-%H%M%S")
# call convert() function to correct the orientation of the object and have the image to display it into the html page
        img= convert('uploads/'+ f_name, l)

        session['axe']=[[1,0,0],[0,1,0],[0,0,1]]
        newname = re.sub('[;, ]', '', f_name)
        os.rename('uploads/'+f_name,'uploads/'+newname)
        session['filename']=newname

        choice=session['choice']
        session['timestr']=timestr
        session['X']=0
        session['Y']=0
        session['z']=0
        session['image']=img


    if session['remember']==2 :
        return render_template('index.html' , img =img.decode('utf8'),X=l, Y=w,Z=h,remember=session['remember'],choices=choice, filename=f_name)
    else:
        return render_template('index.html' , img =img.decode('utf8'),X=l, Y=w,Z=h,remember=session['remember'], choices=[],filename=f_name)


# Show modification on the part after rotation
@app.route('/rotate', methods=['POST','GET'])
def rotate():
    #after redirection to this page the rotation add_collection3d we collect the rotation angles
    x = request.form["x"]
    y = request.form["y"]
    z = request.form["z"]


    choice=session['choice']
    l=session['dimentions'][0]
    timestr=session['timestr']
    f_name=session['filename']
    axe=session['axe']

    img,axx=rotation(f_name,timestr,x,y,z,l,axe)
    session['image']=img
    session['axe']=axx
    session['X']=x
    session['Y']=y
    session['z']=z



    a=img.decode('utf8')

    if session['remember']==2 :
        return render_template('index.html' , img =a,X=l, Y=session['dimentions'][1],Z=session['dimentions'][2],remember=session['remember'],choices=choice,filename=f_name)
    else:
        return render_template('index.html' ,img =a, X=l, Y=session['dimentions'][1],Z=session['dimentions'][2], remember=session['remember'], choices=[],filename=f_name)


if __name__=='__main__':
    app.debug=True
    app.run()
