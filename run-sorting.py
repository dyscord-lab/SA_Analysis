
# import libraries that we need
import csv
import gc
import os
import glob
from datetime import datetime
import pandas as pd

# import custom-made things that we'll need
from sorting import Sorting, nesteddicts_inlist, simplefilechecker, loggaze_matchup

#-------- FILE PATHS SETUP --------#

# NOTE!! This script should be ideally be placed at the top level of a participant's directory
# That is what determines the "root" filepath!

# After my 2 exams i'll make sure to implement a thing that is more interactive
# or potentially a batch mode? if that's desired.
#-=================================#

# set root to current path location
top_root = os.path.join(os.getcwd(), 'realparticipant_data')

# figure out the participants in the directory
included_participants = [participant for participant in os.listdir(top_root)
                        if os.path.isdir(os.path.join(top_root,participant))]

# set or create directory for saving logs
savelogs = os.path.join(os.getcwd(), 'savelogs')
if not os.path.exists(savelogs):
    os.makedirs(savelogs)

# cycle through participants
for next_participant in included_participants:

    # set participant's working directory
    root = os.path.join(top_root,next_participant)

    # TODO: make testdata directory selection more flexible

    # get testdata
    testdata = os.path.join(root,'000').replace('\\', '/')

    # look for the exports folder
    exportfolder = os.path.join(testdata, 'exports', '000').replace('\\', '/')

    # create paths for required participant output files
    logfile = glob.glob(root+'/*.log')[0]

    # TODO: implement a check to make sure there's no more than 1 logfile

    #logfile = os.path.join(root, '000', 'sa1_2019-10-19_000-1.log').replace('\\', '/')
    exportinfo = os.path.join(exportfolder, 'export_info.csv').replace('\\', '/')

    # grab info file
    infofile = os.path.join(testdata, 'info.csv').replace('\\', '/')

    # gaze/position file paths
    gazesurface_file = glob.glob(exportfolder+'/surfaces/gaze_positions*.csv')[0]
    surfaceevents = os.path.join(exportfolder, 'surfaces', 'surface_events.csv').replace('\\', '/')

    sort = Sorting(infofile, savelogs)
    sort.sortsurfaces(surfaceevents)

    # imggaze_chunks = { chunk# : { colname : value } }
    # ie { 000 : { 'world_timestamp' : 123123, ....,.. 'y_scaled': 0.99453 }
    imggaze_chunks = sort.gazesort(gazesurface_file)  # type: dict
    fullinfo = sort.logsort(logfile)  # type:list

    gazes = nesteddicts_inlist(imggaze_chunks)
