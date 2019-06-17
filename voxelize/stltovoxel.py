import argparse
import os.path
import io
import xml.etree.cElementTree as ET
from zipfile import ZipFile
import zipfile

from PIL import Image
import numpy as np

import voxelize.slice as slice
import voxelize.stl_reader as stl_reader
import voxelize.perimeter as perimeter
from voxelize.util import arrayToWhiteGreyscalePixel, padVoxelArray


def doExport(inputFilePath, resolution):
    mesh = list(stl_reader.read_stl_verticies(inputFilePath))
    (scale, shift, bounding_box) = slice.calculateScaleAndShift(mesh, resolution)
    mesh = list(slice.scaleAndShiftMesh(mesh, scale, shift))
    #Note: vol should be addressed with vol[z][x][y]
    vol = np.zeros((bounding_box[2],bounding_box[0],bounding_box[1]), dtype=bool)
    for height in range(min(80,bounding_box[2])):
        print('Processing layer %d/%d'%(height+1,bounding_box[2]))
        lines = slice.toIntersectingLines(mesh, height*(bounding_box[2]/80))
        prepixel = np.zeros((bounding_box[0], bounding_box[1]), dtype=bool)
        perimeter.linesToVoxels(lines, prepixel)
        vol[height] = prepixel
    return exportNumpy(vol)



def exportNumpy(logicalVoxelArray):
    print(logicalVoxelArray.shape)
    voxelArray = np.zeros((80,80,80))

    for i in range(logicalVoxelArray.shape[0]):
        for j in range(logicalVoxelArray.shape[1]):
            for k in range(logicalVoxelArray.shape[2]):
                if logicalVoxelArray[i, j, k]:
                    voxelArray[i, j, k] = 1
    return voxelArray

def file_choices(choices,fname):
    filename, ext = os.path.splitext(fname)
    if ext == '' or ext not in choices:
        if len(choices) == 1:
            parser.error('%s doesn\'t end with %s'%(fname,choices))
        else:
            parser.error('%s doesn\'t end with one of %s'%(fname,choices))
    return fname

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert STL files to voxels')
    parser.add_argument('input', nargs='?', type=lambda s:file_choices(('.stl'),s))
    parser.add_argument('output', nargs='?', type=lambda s:file_choices(('.png', '.xyz', '.svx','.np'),s))
    args = parser.parse_args()
