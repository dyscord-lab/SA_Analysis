# import libraries that we need
import csv
import os
import glob
from datetime import datetime
import pandas as pd

# import custom-made things that we'll need
from sorting import Sorting, chunks, process_surfaces, pair_logs, associate_gaze_stimulus
from filesearch import findparticipants, findhighest, findlogfile, findinfofile

# set root to current path location
top_root = os.path.join(os.getcwd(), 'data')

# set or create directory for saving logs
savelogs = os.path.join(os.getcwd(), 'savelogs')
if not os.path.exists(savelogs):
    os.makedirs(savelogs)

# keeps track of any issues and saves to file at end
issues = {}

# figure out the participants in each sub-directory
# each participant = full path to their datafolder
included_participants = findparticipants(dataroot)

# cycle through participants
for next_participant in included_participants:

    # set participant's working directory
    root = next_participant

    # sets participant info for documentation purposes
    participant = os.path.split(root)[1]
    day = os.path.split(os.path.split(root)[0])[1]
    participant_info = str(participant) + '_' + str(day)

    # identify the info file path
    infofile = findinfofile(root)

    # create paths for required participant output files
    logfile = findlogfile(root)
    if type(logfile) == list:
        # if multiple log files found, documents as issue and skip this participant
        issues[participant_info] = logfile
        continue

    # look for the exports folder
    exportfolder = findhighest(os.path.join(root, 'exports'))

    # identify the export info file path
    exportinfo = os.path.join(exportfolder, 'export_info.csv')

    # gaze/position file paths
    gazesurface_file = glob.glob(exportfolder + '/surfaces/gaze_positions*.csv')[0]
    surfaceevents = os.path.join(exportfolder, 'surfaces', 'surface_events.csv')

    # sort the info file
    sort = Sorting(infofile, savelogs)

    # process the surface file
    processed_surfaces = process_surfaces(surfaceevents)

    # process the logfile
    processed_logs = sort.logsort(logfile)

    # associate the surface and log stimulus information
    paired_logs = pair_logs(processed_surfaces, processed_logs)

    # associate the gaze data with the stimulus data
    gaze_stimulus_df = associate_gaze_stimulus(gazesurface_file, paired_logs)

    # save the final dataframe
    filename = participant_info + '_complete_gaze_df.csv'
    gaze_stimulus_df.to_csv(savelogs + '/' + filename, index=None)


# logs issues, if there are any
# right now just for ".log" duplicates, more can be added though
if issues:
    date = str(datetime.now())

    issuesfile = savelogs + '/issues.csv'
    mode = "w+"
    if os.path.exists(issuesfile):
        mode = "a"

    with open(issuesfile, mode, newline='') as f:
        writer = csv.writer(f)
        for participant, issue in issues.items():
            writer.writerow([participant, issue])