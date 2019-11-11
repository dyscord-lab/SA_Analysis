# import libraries that we need
import glob
import os
import pandas as pd

# import custom-made functions that we'll need
from lib.sorting import Sorting, process_surfaces, merge_all_dataframes, extract_survey
from lib.filesearch import find_participants, find_highest_export

# set root to current path location
top_root = os.path.join(os.getcwd(), 'data')

# set or create directory for saving logs
savelogs_directory = os.path.join(os.getcwd(), 'savelogs')
if not os.path.exists(savelogs_directory):
    os.makedirs(savelogs_directory)

# keeps track of any issues and saves to file at end
issues = pd.DataFrame(columns=['participant', 'error'])

# figure out the participants in each sub-directory
# each participant = full path to their datafolder
included_participants = find_participants(top_root)

# cycle through participants
for next_participant in included_participants:

    # set participant's working directories
    root = next_participant
    containing_directory = os.path.abspath(os.path.join(root, "../"))

    # sets participant info for documentation purposes
    participant = os.path.split(root)[1]
    day = os.path.split(os.path.split(root)[0])[1]
    participant_info = str(participant) + '_' + str(day)

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

    # # TODO: this could be a cleaner kind of solution -- need to update find_logfile
    # logfile = find_logfile(root)
    # if isinstance(logfile_path, list):
    #     # multiple log files found,
    #     # documents as issue and skip this participant
    #     issues.append({'participant': participant_info,
    #                    'error': logfile_path}, ignore_index=True)
    #     continue

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
    [full_logfile, processed_img_logs] = sort.logsort(logfile_path)
    
    # adjust the timestamps for gaze on recognized surfaces
    gaze_surface_df = pd.read_csv(gazesurface_path)
    gaze_surface_df = sort.adjust_timestamps(gaze_surface_df, processed_img_logs)

    # adjust the timestamps for all recorded gaze
    processed_surfaces['adjusted_timestamp'] = ((processed_surfaces['gaze_timestamp'] + sort.offset)
                                                 .round(4))
    
    # join the gaze and PsychoPy image log data
    gaze_dataframe = merge_all_dataframes(processed_surfaces, gaze_surface_df, processed_img_logs)

    # extract the survey data
    survey_df = extract_survey(full_logfile)

    # save the final gaze dataframe
    gaze_filename = participant_info + '-complete_gaze_df.csv'
    gaze_dataframe.to_csv(savelogs_directory + '/' + gaze_filename,
                                    index=None)

    # save the final survey dataframe
    survey_filename = participant_info + '-survey_df.csv'
    survey_df.to_csv(savelogs_directory + '/' + survey_filename, index=None)

# logs issues, if there are any
# right now just for ".log" duplicates, more can be added though
issues.to_csv(savelogs_directory+'/issues.csv',
              index=None)
