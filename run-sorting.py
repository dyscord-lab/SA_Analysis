# import libraries that we need
import glob, os, re
import pandas as pd

from lib.export import export_files
from lib.filesearch import find_participants, find_highest_export
# import custom-made functions that we'll need
from lib.sorting import Sorting, process_surfaces, merge_all_dataframes, extract_survey

# set root to current path location
top_root = os.path.join(os.getcwd(), 'data')

# set or create directory for saving logs
savelogs_directory = os.path.join(os.getcwd(), 'data', 'analysis')
if not os.path.exists(savelogs_directory):
    os.makedirs(top_root + "/processed")
    os.makedirs(top_root + "/analysis")

# keeps track of any issues and saves to file at end
issues = pd.DataFrame(columns=['participant', 'error'])

# read in survey key
survey_key = pd.read_csv('./lib/survey_key-SA.csv')

# figure out the participants in each sub-directory
# each participant = full path to their datafolder
included_participants = find_participants(os.path.join(top_root, "raw"))

# cycle through participants
for next_participant in included_participants:

    # set participant's working directories
    root = next_participant
    containing_directory = os.path.abspath(os.path.join(root, "../"))

    # sets participant info for documentation purposes
    participant_info = re.sub("_pupil", "",
                              os.path.split(containing_directory)[1])

    # identify log file path
    try:
        logfile_path = glob.glob(containing_directory + '/*.log')[0]
    except IndexError:
        # a .log file wasn't found in the participants directory
        # aka index [0] doesn't exist, so document issue and continue to next?
        issues.append(
            {'participant': participant_info,
             'error': 'logfile not found/glob list empty'},
            ignore_index=True)
        continue

    try:
        infofile_path = glob.glob(containing_directory + './info.csv')[0]
    except IndexError:
        issues.append(
            {'participant': participant_info,
             'error': 'info.csv not found/glob list empty'},
            ignore_index=True)
        continue

    # look for the exports folder
    exportfolder_path = find_highest_export(os.path.join(root, 'exports'))

    # gaze/position file paths
    full_gaze_path = glob.glob(exportfolder_path + '/gaze_positions.csv')[0]
    gazesurface_path = glob.glob(exportfolder_path + '/surfaces/gaze_positions*.csv')[0]
    surfaceevents_path = os.path.join(exportfolder_path, 'surfaces', 'surface_events.csv')

    # initialize the Sort class
    sort = Sorting(savelogs_directory)

    # process the surface file
    processed_surfaces = process_surfaces(surfaceevents_path, full_gaze_path)

    # process the logfile
    [full_logfile, processed_img_logs] = sort.logsort(logfile_path, infofile_path)

    # adjust the timestamps for gaze on recognized surfaces
    gaze_surface_df = pd.read_csv(gazesurface_path)
    gaze_surface_df = sort.adjust_timestamps(gaze_surface_df, processed_img_logs)

    # adjust the timestamps for all recorded gaze
    processed_surfaces['adjusted_timestamp'] = ((processed_surfaces['gaze_timestamp']
                                                 + sort.offset)
                                                .round(4))

    # join the gaze and PsychoPy image log data
    gaze_dataframe = merge_all_dataframes(processed_surfaces,
                                          gaze_surface_df,
                                          processed_img_logs)

    # extract the survey data
    survey_df = extract_survey(full_logfile, survey_key)

    # export everything
    export_files(participant_info,
                 top_root,
                 gaze_dataframe,
                 survey_df)

# logs issues, if there are any
# right now just for ".log" duplicates, more can be added though
issues.to_csv(top_root + '/issues.csv',
              index=None)
