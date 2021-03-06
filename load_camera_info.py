#!/usr/bin/env python3

import pathlib
from pathlib import Path
import numpy

def load_halcon_intrinsics(filePath):
    """ Load a halcon camera intrinsics file.
            i.e. the human-readable ASCII ones starting with \"ParGroup\"
        This function just does a 1:1 mapping of the (badly documented)
        file contents into python.
        Input:
            filePath -- The name of the file to read
        Output:
            A dictionary containing the focal length,
            radial distortion polynomial coefficients, etc...
            """
    lines = filePath.open().readlines()
    lines = map(lambda line: line.strip(), lines)
    lines = filter(lambda line: line != '', lines)
    lines = filter(lambda line: line[0] != '#', lines)
    lines = map(lambda line: line.strip(), lines)
    lines = list(lines)

    # remove ParGroup header
    assert (lines[0].startswith('ParGroup'))
    currentLine = 2
    expectedNames = ['Focus', 'Poly1', 'Poly2', 'Poly3', 'Poly4', 'Poly5',
                     'Sx', 'Sy', 'Cx', 'Cy', 'ImageWidth', 'ImageHeight']
    expectedNameIndex = 0
    d = {}
    while currentLine < len(lines) and expectedNameIndex < len(expectedNames):
        line = lines[currentLine]
        expectedName = expectedNames[expectedNameIndex]
        assert (line.startswith(expectedName))
        value_string = line.split(':')[2].split(';')[0]
        value = float(value_string)
        currentLine += 3
        expectedNameIndex += 1
        d[expectedName] = value
    return d


def load_intrinsics(filePath):
    """ Load and convert the HALCON representation of the camera matrix
        into the representation closer to that used by open source
        programs.
        Input:
            filePath -- The name of the file to read
        Output:
            The 3x3 camera projection matrix K and distortion coefficients.
            x_pixel_homogeneous = K*x_world
        """
    d = load_halcon_intrinsics(filePath)
    cameraMatrix = numpy.zeros([3, 3])

    fx = d['Focus'] / d['Sx']
    fy = d['Focus'] / d['Sy']
    cameraMatrix[0, 0] = fx
    cameraMatrix[1, 1] = fy

    cx = d['Cx']
    cy = d['Cy']
    cameraMatrix[0, 2] = cx
    cameraMatrix[1, 2] = cy
    cameraMatrix[2, 2] = 1.0

    k1 = d['Poly1']
    k2 = d['Poly2']
    k3 = d['Poly3']
    p1 = d['Poly4'] * .001
    p2 = d['Poly5'] * .001
    distCoffs = (k1, k2, p1, p2, k3)

    return cameraMatrix, distCoffs

def load_extrinsics(filePath):
    """ HALCON is able to export camera extrinsics as a homogeneous matrix
        stored in an ascii text file. This export format is the easies to deal
        with.
        Input:
        filePath -- The path of the text file containing the homogeous matrix
        Output:
        The Rotation matrix and Translation vector associated with the camera.
        The matrices are for the transformation from the camera frame to
        world coordinate frame, i.e. x_world = R*x_camera + T
        T is in whatever units the camera calibration was done in (usually meters).
        If you need the transformation in the other direction you can do:
        R,T = R.T,numpy.dot(-R.T,T) # Invert the transform
        """
    strings = filePath.open().readlines()[0].strip().split(' ')
    assert len(strings)==12
    H = numpy.array(tuple(map(float,strings))).reshape((3,4))
    R = H[:,0:3]
    T = H[:,3]
    return R, T
