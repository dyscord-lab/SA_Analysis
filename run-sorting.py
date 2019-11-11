# import libraries that we need
import glob
import os
import pandas as pd

# import custom-made functions that we'll need
from lib.filesearch import findparticipants, findhighest
from lib.sorting import Sorting, process_surfaces, pair_logs, associate_gaze_stimulus, extract_survey

# set root to current path location
top_root = os.path.join(os.getcwd(), 'data')

# set or create directory for saving logs
savelogs = os.path.join(os.getcwd(), 'savelogs')
if not os.path.exists(savelogs):
    os.makedirs(savelogs)

# keeps track of any issues and saves to file at end
issues = pd.DataFrame(columns=['participant', 'error'])

# figure out the participants in each sub-directory
# each participant = full path to their datafolder
included_participants = findparticipants(top_root)

# cycle through participants
for next_participant in included_participants:

    # set participant's working directories
    root = next_participant
    containing_directory = os.path.abspath(os.path.join(root, "../"))

    # sets participant info for documentation purposes
    participant = os.path.split(root)[1]
    day = os.path.split(os.path.split(root)[0])[1]
    participant_info = str(participant) + '_' + str(day)

    # # identify the info file path
    # infofile = root + '/info.csv'

    # identify log file path
    try:
        logfile = glob.glob(containing_directory + '/*.log')[0]
    except IndexError:
        # a .log file wasn't found in the participants directory
        # aka index [0] doesn't exist, so document issue and continue to next?
        issues.append(
            {'participant': participant_info,
             'error': 'logfile not found/glob list empty'},
            ignore_index=True)
        continue

    # logfile = findlogfile(root)
    # if isinstance(logfile, list):
    #     # multiple log files found,
    #     # documents as issue and skip this participant
    #     issues.append({'participant': participant_info,
    #                    'error': logfile}, ignore_index=True)
    #     continue

    # look for the exports folder
    exportfolder = findhighest(os.path.join(root, 'exports'))
    print(exportfolder)

    # identify the export info file path
    exportinfo = os.path.join(exportfolder, 'export_info.csv')

    # gaze/position file paths
    gazesurface_file = glob.glob(exportfolder + '/surfaces/gaze_positions*.csv')[0]
    surfaceevents = os.path.join(exportfolder, 'surfaces', 'surface_events.csv')

    # sort the info file
    sort = Sorting(savelogs)

    # process the surface file
    processed_surfaces = process_surfaces(surfaceevents)

    # see if we processed the file
    if isinstance(processed_surfaces, str):

        # if we have incomplete data, flag the participant
        issues = issues.append({'participant': participant_info,
                                'error': processed_surfaces},
                               ignore_index=True)

    # if we have the data, process proceed
    else:
        # process the logfile
        [full_logfile, processed_img_logs] = sort.logsort(logfile)

        # associate the surface and log stimulus information
        paired_logs = pair_logs(processed_surfaces, processed_img_logs)

        # see if we were able to process everything
        if isinstance(paired_logs, str):

            # if we have incomplete data, flag the participant
            issues = issues.append({'participant': participant_info,
                                    'error': paired_logs},
                                   ignore_index=True)

        # if we have the data, proceed
        else:

            # associate the gaze data with the stimulus data
            gaze_stimulus_df = associate_gaze_stimulus(gazesurface_file,
                                                       paired_logs)

            # extract the survey data
            survey_df = extract_survey(full_logfile)

            # save the final gaze dataframe
            gaze_filename = participant_info + '-complete_gaze_df.csv'
            gaze_stimulus_df.to_csv(savelogs + '/' + gaze_filename,
                                    index=None)

            # save the final survey dataframe
            survey_filename = participant_info + '-survey_df.csv'
            survey_df.to_csv(savelogs + '/' + survey_filename, index=None)

# logs issues, if there are any
# right now just for ".log" duplicates, more can be added though
issues.to_csv(savelogs+'/issues.csv',
              index=None)
