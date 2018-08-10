import logging
import os
import sys

import maya.cmds as cmds
import avalon

from avalon.maya import lib

log = logging.getLogger("img2exr Maya Lib")


def get_file_texture_nodes():
    """
    Find all file texture nodes in scene and return their dag path
    Args:
        self:

    Returns:

    """
    files = cmds.ls(type='File', l=True) or []
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
    path = 'C:/Program Files/Chaos Group/V-Ray/Maya {} for x64/bin/img2tiledexr.exe'.format(maya_version)
    return path
