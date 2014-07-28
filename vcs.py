#! /usr/bin/env python

# a command line version control system
from shutil import copy, copytree, rmtree, ignore_patterns
import os, sys
import argparse
import sqlite3
import datetime, time

# src and dst_root can't have trailing backslash
def snapshot(message='', src=".", dst_root=".myvcs"):
    """
    Copies everything in src/ to dst_root/x/ where x is the xth snapshot, or the xth call to this function with the same src and dst params; x is 0-indexed
    """
    
    # in the case that there are no snapshots, the return value of last_version_num is -1, so incrementing will bring it to 0, which is what we want
    next_number = last_version_num(dst_root) + 1

    dst = dst_root + '/' + str(next_number)
    copytree(src, dst, ignore=ignore_patterns('.myvcs'))
    log_current(next_number)
    log(next_number, message)
    print "created snapshot # " + str(next_number)

def copy_dir_unsafe(src, dst):
    try:
        copytree(src, dst)
    except OSError:
        # dst dir already exists; overwrite it
        rmtree(dst)
        copytree(src, dst)
    print "unsafe copied"

# target and vc_dir can't have trailing backslash
# TODO : delete stuff currently in target that wasn't there in the snapshot
def revert(version, target=".", vc_dir=".myvcs"):
    """
    Reverts the target directory to a previous snapshot
    """
    src = vc_dir + '/' + str(version)

    # can't just use copytree to copy vc_dir/version/ to target b/c copytree requires that target not exist and we can't just remove it first because target might contain vc_dir, so we need to manually copy every file/dir from the snapshot to target
    try:
        # files and dir of past snapshot to copy over
        to_copy = os.listdir(src)
        
        for thing in to_copy:
            copy(src + '/' + thing, target + '/')
    except OSError:
        print "Error"
    log_current(version)
    print "reverted to version: " + str(version)

def last(target=".", vc_dir=".myvcs"):
    """
    Reverts target to the latest snapshot
    """
    last_version = last_version_num(vc_dir)
    revert(last_version, target, vc_dir)
    log_current(last_version)



"""
Metadata stuff
"""
def init(vc_dir='.myvcs', db_name='metadata.db'):
    """ 
    Creates a new sqllite3 database for the per-snapshot data. 
    
    If this function has already called, or a metadata file already exists, prints message and does nothing
    """
    
    # in case vc_dir doesn't exist, otherwise sql will throw error
    if not os.path.exists(vc_dir):
        os.makedirs(vc_dir)

    conn = sqlite3.connect(vc_dir + '/' + db_name)
    cur = conn.cursor()
    
    try:
        # Create table
        cur.execute('''CREATE TABLE snapshots 
                       (version integer, timestamp timestamp, message text)''')
        conn.commit()
    except sqlite3.OperationalError:
        print 'Repo has already been init. Metadata file already exists: ' + vc_dir + '/' + db_name

    conn.close()
    
def log(version, message='', vc_dir='.myvcs', db_name='metadata.db'):
    """
    Logs the timestamp and optional message of the version-th snapshot in the sqllite3 metadata file
    """
    conn = sqlite3.connect(vc_dir + '/' + db_name)
    cur = conn.cursor()
    
    now = datetime.datetime.now()

    cur.execute('''insert into snapshots 
                   (version, timestamp, message) values (?, ?, ?)''', 
                (version, now, message))
    
    conn.commit()
    #except sqlite3.OperationalError:
        # Most likely table doesn't exist, meaning init hasn't been called yet
    #    print "Please use the 'init' command before making any snapshots"

    conn.close()

def fetch_logs(vc_dir='.myvcs', db_name='metadata.db'):
    """
    Get all log info stored in the database and return it.
    
    If database throws error, returns None
    """
    conn = sqlite3.connect(vc_dir + '/' + db_name)
    cur = conn.cursor()
    
    logs = None
    try:
        logs = cur.execute('select * from snapshots').fetchall()
    except sqlite3.OperationalError:
        print "Please use the 'init' command before fetching logs"

    conn.close()
    return logs
    
def log_current(version, vc_dir=".myvcs", metafile='head'):
    """
    Log the current working version in the metadata at vc_dir/metafile
    """
    file = open(vc_dir + '/' + metafile, 'w')
    file.write(str(version))
    file.close()

def get_current(vc_dir=".myvcs", metafile="head"):
    """
    Returns the version number stored in vc_dir/head
    """
    file = open(vc_dir + '/' + metafile, 'r')
    num = file.readline()
    file.close()
    return num
    


"""
Utils
"""
def last_version_num(vc_dir=".myvcs"):
    """ 
    Returns the version number of the last snapshot in vc_dir. 
    Returns -1 if no snapshots found. 
    
    Figures out current number by looking for highest number used.
    No guarantees of correctness if vc_dir is corrupted 
    (dirs created in dst_root by other things/people)
    """
    # number to return
    next_number = -1
    try: 
        # OSErro when dst_root dir doesn't exist, ie no snapshots created yet
        existing = os.listdir(vc_dir)
        
        # create list of dir names that are ints; 
        # silently ignore other dir/files
        nums = []
        for dir_name in existing:
            try:
                nums.append(int(dir_name))
            except ValueError:
                 continue

        # sort in highest-num order and get first elem
        nums = sorted(nums, reverse=True)

        # possible IndexError
        next_number = nums[0]
    except (IndexError, OSError):
        # list was empty or dst_root doesn't exist = no snapshots created yet
        pass
    return next_number



"""
 wrappers for the actual functions in order to extract the info from the parser Namespace object
"""
def init_wrapper(args):
    # init command takes no arguments so args should be empty Namespace
    init()

def snapshot_wrapper(args):
    if args.message:
        snapshot(args.message[0])
    else:
        snapshot()

def revert_wrapper(args):
    revert(args.version)

def last_wrapper(args):
    # latest command takes no arguments so args should be empty Namespace
    latest()

def current_wrapper(args):
    print get_current()

def log_wrapper(args):
    history = fetch_logs()
    if history is None:
        return
    for log in history:
        print log
    
if __name__ == "__main__":
    # create the arguments parser; each operation is an individual subcommand
    parser = argparse.ArgumentParser(description='local version control')
    subparsers = parser.add_subparsers()
    
    parser_snap = subparsers.add_parser(
        'init',
        help='initialize the metadata for this repo')
    parser_snap.set_defaults(func=init_wrapper)

    parser_snap = subparsers.add_parser(
        'snap',
        help='create a snapshot of the current directory')
    parser_snap.add_argument(
        "-m", "--message", 
        nargs=1,
        help="message associated with this snapshot")
    parser_snap.set_defaults(func=snapshot_wrapper)

    parser_checkout = subparsers.add_parser(
        'checkout',
        help='checkout a previous snapshot into the current directory')
    parser_checkout.add_argument(
        'version', type=int, 
        help='version to revert to')
    parser_checkout.set_defaults(func=revert_wrapper)

    parser_latest = subparsers.add_parser(
        'last',
        help='checkout the last snapshot')
    parser_latest.set_defaults(func=last_wrapper)
    
    parser_latest = subparsers.add_parser(
        'current',
        help='print the version number of the current snapshot')
    parser_latest.set_defaults(func=current_wrapper)

    parser_snap = subparsers.add_parser(
        'log',
        help='print out the log of snapshots including timestamps and messages')
    parser_snap.set_defaults(func=log_wrapper)

    # args is a Namespace object so there are wrappers for each function to extract the relevant fields and call the actual functions
    args = parser.parse_args()
    # each parser has a default function associated with it, which will be called with .func
    args.func(args)
