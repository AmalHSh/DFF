# DFF

# Requirements

You need to have python 3.6 on your laptop.
You can also set up anaconda environment.


### Installation
redirect to the Data-Collector folder open a terminal and go to your working environment:
first you need install all requirements

```sh
$ cd  folder_path/DFF
$ pip install -r requirements.txt
```

### Installation
To make the application running:
Before running the application go to utils.py and change some paths. Then, you can start the application.

```sh
$ python app.py
```
And open tour favorite browser go to localhost:5000.

### Folder contents

In this folder there are some important files and folders

- app.py: this file has the function controlling the html page
- data.csv: is the file where the data is stored
- utils.py: is the file from where the app.py call the functions.
It has the upload function, rotation and visualization.
- voxelize: this folder has all the functions responcible for the voxelization of the mesh
- static: This folder has the css and javascript code and some pictures loaded from the html page.
- templates: this folder has all the html pages
- uploads: is the folder where all the uploaded stl files are stored

