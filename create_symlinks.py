#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import os
import re
import struct


XFFTS_DIR = os.path.expanduser("/export/log/xffts")
LINKS_DIR = os.path.expanduser("/export/log/xffts_links")
XFFTS_PATTERN = r"^xffts2018(09|10)[0-9]{8}\.xfftsx\.0[1-4]$"


def is_exists(path):
    """Check whether the specified path exists"""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise FileNotFoundError("{path}: not found".format(path=path))

    return path
    

def create_symlink(path):
    """Create symlinks of XFFTS raw data (add obsnum)"""
    path = is_exists(path)

    with open(path, "rb") as f:
        f.seek(32)
        obsnum_bin = f.read(8)
    
    try:
        obsnum = struct.Struct("q").unpack(obsnum_bin)[0]
    except struct.error:
        obsnum = "no_lmt"

    fname = os.path.basename(path)
    new_fname = "{obsnum}_{fname}".format(obsnum=obsnum, fname=fname)
    
    new_path = os.path.expanduser(
        "{links_dir}/{new_fname}".format(
            links_dir=LINKS_DIR,
            new_fname=new_fname
        )
    )

    try:
        os.symlink(path, new_path)
    except OSError:
        print("{new_path}: already exists".format(new_path=new_path))

    return


if __name__ == "__main__":
    pattern = re.compile(XFFTS_PATTERN)
    for xffts in os.listdir(XFFTS_DIR):
        if pattern.match(xffts):
            create_symlink(XFFTS_DIR + "/" + xffts)
