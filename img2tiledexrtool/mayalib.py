"""
This module contains the script that ui app uses to communicate with Maya

TODO: We might be able to simply check for state without the int attr:
If we use the current fileTexName (A) and compare with the stored
fileTexNameSource (B) we can conclude that if B == None, we have no
conversion, if A == B we have a conversion but are viewing the non
converted file, if A != B and A.endswith.exr we have a conversion and we are
viewing the exr.
"""
import logging
import os
import sys

import maya.cmds as cmds

from . import img2tiledexrtool

#reload(img2tiledexrtool)

log = logging.getLogger("img2exr Maya Lib")

def get_file_texture_model_data():
    """
    Creates a list with tuples that contain the tiledEXR attr state,
    node name and file fileTextureName.

    Returns:
        list of tuples with state attr, maya node, file path

    """
    filenodes = get_file_texture_nodes()
    data = []
    """ 0 = Not converted before, 1 = converted, but not active, 2 = converted and active (exr is current file)"""
    for node in filenodes:
        attr = 0
        if cmds.attributeQuery('tiledEXR', node=node, exists=True):
            attr = cmds.getAttr('{}.tiledEXR'.format(node))
        data.append(
            (attr, node, cmds.getAttr('{}.fileTextureName'.format(node))))
    return data


def get_file_texture_nodes():
    """
    Find all file texture nodes in scene and return their dag path

    If the user has made a selection, the file nodes from that selection are
    used, otherwise we show all file nodes in scene.

    Args:
        self:

    Returns:
        list with file node names

    """
    files = cmds.ls(sl=True, type='file', l=True) or cmds.ls(type='file', l=True) or []
    return files


def get_maya_install_dir():
    """
    Retarded way of finding from where our current maya is running from
    Args:
        self:

    Returns:
        string with maya bin path
    """
    for p in sys.path:
        ps = os.path.split(p)
        if ps[-2].startswith('maya') and ps[-1] == 'bin':
            return p


def mark_for_conversion(filenodes=[]):
    """
    Not used at the moment
    Args:
        filenodes:

    Returns:

    """
    conversion_collection = []
    for node in filenodes:
        source = cmds.getAttr('{}.fileTextureName'.format(node))
        attr = 0
        if cmds.attributeQuery('tiledEXR', node=node, exists=True):
            """ This node has been converted before"""
            attr = 2 if cmds.getAttr('{}.tiledEXR'.format(node)) else 1

        if attr == 0:
            cmds.addAttr(node, longName='tiledEXR', minValue=0, maxValue=2,
                         at='byte')
            cmds.setAttr('{}.tiledEXR'.format(node), 1)
            # Everytime I'm amazed at what an inconsistent mess cmds is.
            cmds.addAttr(node, longName='tiledEXRSource', dt='string')
            cmds.setAttr('{}.tiledEXRSource'.format(node), source)
            attr = 1

        if attr == 2:
            source = cmds.getAttr('{}.tiledEXRSource'.format(node))

        conversion_collection.append((node, source))

    #(conversion_collection)
    return conversion_collection


def convert_files(executable_path, data, preserve, postfix='_tiled', threads=8,
                  overwrite=False, compression='zips', tile_size=64,
                  linear='off', preserver_filter=''):
    """
    Convert a list of files to tiled exrs

    Args:
        overwrite (bool): Overwrite existing files?
        compression (str): EXR compression type, allowed values: 'none', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44', 'b44a', 'dwaa', 'dwab'
        tile_size (int): Size of the tiles
        linear (str): Convert color space to linear, allowed values: 'auto', 'on', 'off'
        threads: how many conversions can run at the same time
        executable_path: file location of vray img2tiledexr executable
        data: list of node tuples (as returned by get_file_texture_model_data)

    Returns:

    """

    file_nodes = zip(*data)[1]
    file_color_spaces = []
    file_paths = []
    preserver_filters = preserver_filter.strip().split(',')
    for node in file_nodes:
        if cmds.attributeQuery('tiledEXRSource', node=node, exists=True):
            file = cmds.getAttr('{}.tiledEXRSource'.format(node))
            if not file or not os.path.exists(file) or not os.path.isfile(file):
                file = cmds.getAttr('{}.fileTextureName'.format(node))
                cmds.setAttr('{}.tiledEXRSource'.format(node), file,
                             type="string")
        else:
            file = cmds.getAttr('{}.fileTextureName'.format(node))

        if file and os.path.exists(file) and os.path.isfile(file):
            file_paths.append(file)
            file_color_spaces.append(cmds.getAttr('{}.colorSpace'.format(node)))

    # start conversion:
    result = img2tiledexrtool.convert_img_2_exr(executable_path, file_paths,
                                                postfix=postfix,
                                                threads=threads,
                                                overwrite=overwrite,
                                                compression=compression,
                                                linear=linear,
                                                tile_size=tile_size)

    # done, reconnect files that converted succesfully and set attributes
    # result should contain a list of tuples containing:
    # ( file_in, file_out, status (None = succes))
    file_paths = list(zip(*data)[2])
    for item in result:
        idx = file_paths.index(item[0])
        if idx is not None:
            node = file_nodes[idx]
            if not cmds.attributeQuery('tiledEXRSource', node=node, exists=True):
                cmds.addAttr(node, longName='tiledEXRSource', dt="string")
            cmds.setAttr('{}.tiledEXRSource'.format(node), item[0], type="string")
            cmds.setAttr('{}.fileTextureName'.format(node), item[1], type="string")
            if not cmds.attributeQuery('tiledEXR', node=node, exists=True):
                cmds.addAttr(node, longName='tiledEXR', min=0, max=2, at='byte', w=False, r=True)
            cmds.setAttr('{}.tiledEXR'.format(node), 2)
            if preserve:
                if any(n in item[1] for n in preserver_filters):
                    cmds.setAttr('{}.colorSpace'.format(node), file_color_spaces[idx], type="string")


def revert_nodes(file_nodes, postfix, set_to_source, preserve,
                 preserver_filter):
    """
    Revert/switch a file node to it's source, or generated exr
    Args:
        preserve: should we restore the file node colorspace settings after
            conversion (when ignore colorspace is off, Maya makes a guess at
            what to set the color space to.)
        file_nodes: list of file nodes
        postfix: the postfix script as used by the converter (to generate the
            final exr file name.
        set_to_source: bool that defines whether or not we need to set to source
            or to the tiled exr

    Returns:

    """

    preserver_filters = preserver_filter.strip().split(',')

    for node in file_nodes:
        if cmds.attributeQuery('tiledEXR', node=node[1], exists=True):
            color_space = cmds.getAttr('{}.colorSpace'.format(node[1]))
            if set_to_source:
                if cmds.attributeQuery('tiledEXRSource', node=node[1], exists=True):
                    source = cmds.getAttr('{}.tiledEXRSource'.format(node[1]))
                    cmds.setAttr('{}.fileTextureName'.format(node[1]), source, type="string")
                    cmds.setAttr('{}.tiledEXR'.format(node[1]), 1)
                    if preserve:
                        if any(n in source for n in preserver_filters):
                            cmds.setAttr('{}.colorSpace'.format(node[1]), color_space, type="string")
            else:
                if cmds.attributeQuery('tiledEXRSource', node=node[1], exists=True):
                    source = cmds.getAttr('{}.tiledEXRSource'.format(node[1]))

                    file = '{}{}.exr'.format(os.path.splitext(source)[0],
                                             postfix)
                    print(color_space)
                    cmds.setAttr('{}.fileTextureName'.format(node[1]), file, type="string")
                    cmds.setAttr('{}.tiledEXR'.format(node[1]), 2)
                    if preserve:
                        if any(n in file for n in preserver_filters):
                            cmds.setAttr('{}.colorSpace'.format(node[1]), color_space, type="string")

def get_tiled_exr_exe_dir():
    """
    Construct a vray img converter path

    We're making a whole bunch of assumptions on this and create the path in
    a very naive way.
    Returns:
        Guestimated path to vray img2tiledexr executable
    """
    # TODO, platform independence
    maya_version = cmds.about(v=True)
    path = 'C:/Program Files/Chaos Group/V-Ray/Maya {} for x64/bin/img2tiledexr.exe'.format(
        maya_version)
    if not os.path.exists(path): path = ""
    return path
