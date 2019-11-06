# import libraries that we need
import csv
import gc
import os
from datetime import datetime
import pandas as pd


# Handles the general sorting
class Sorting():
    def __init__(self, expInfo, savelogs):
        self.imgsorder = []
        self.surfaces = []
        self.savelogs = savelogs

    def logsort(self, log_file_path):

        """ Parse the PsychoPy logfile."""

        # read in the file as a dataframe
        fullinfo = (pd.read_csv(log_file_path, sep='\t', header=None)

                      # rename columns
                      .rename(columns={0:"start_time",
                                       1:"type",
                                       2:"event"})

                      # drop any participant responses
                      .dropna())

        # get the end time for each screen
        fullinfo['end_time'] = fullinfo['start_time'].shift(-1)

        # get duration for each screen
        fullinfo['duration'] = (pd.to_numeric(fullinfo['end_time']) -
                                pd.to_numeric(fullinfo['start_time']))


        # identify only the events where images occurred
        only_pics = (fullinfo[fullinfo['event'].str.contains("PICTURE")]
                                .reset_index(drop=True)
                                .drop(columns='type')
                                .rename(columns={'event': 'picture'}))

        # leave only picture numbers for picture identification
        only_pics['picture'] = (only_pics['picture'].str.replace('PICTURE: ','')
                                                    .str.replace('.png',''))

        # save image order
        self.imgsorder = [int(x) for x in only_pics.picture.unique()
                          if x != "reset_image"]

        # return the picture dataframe
        return fullinfo, only_pics

def chunks(l, n):
    """Convert a list l into chunks of n size.
        Credit to Ned Batchelder: https://stackoverflow.com/a/312464"""

    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):

        # Create an index range for l of n items:
        yield l[i:i+n]

def process_surfaces(surface_events_path):
    """Process surface events file from Pupil Player."""

    # read surface events file to dataframe
    surface_info = (pd.read_csv(surface_events_path)
                     .drop(columns='surface_name'))

    # sequence surface names and events
    surface_info['surface_num'] = surface_info.groupby('event_type').cumcount()+1

    # concatenate variables
    surface_info['surface_and_event'] = (surface_info['event_type']
                                        + '_'
                                        + surface_info['surface_num'].map(str))

    # get the start time, end time, and duration for each surface event
    surface_info = surface_info.rename(columns={'world_timestamp': 'start_time'})
    surface_info['end_time'] = surface_info['start_time'].shift(-1)
    surface_info['duration'] = (pd.to_numeric(surface_info['end_time']) -
                                pd.to_numeric(surface_info['start_time']))

    # if a frame took less than the appropriate amount of time, try to pair it
    interrupted_frames = surface_info[(surface_info['event_type']=='enter') &
                                      (surface_info['duration'] < 1.95)]

    # if there aren't any interrupted frames, continue on
    if len(interrupted_frames)==0:
        del interrupted_frames

    # if there are an odd number of interrupted frames, stop
    elif len(interrupted_frames)%2!=0:
        raise ValueError('An odd number of interrupted frames have been flagged.')

    # if there are an even number of interrupted frames, pair them
    else:

        # TODO: Implement check to make sure the 2 observed times add up to ~2 sec

        # identify the surface numbers of partial frames and pair them
        partial_frames = interrupted_frames.surface_num.unique()
        identified_pairs = list(chunks(partial_frames, 2))

        # rename pairs in the original df
        for pair in identified_pairs:

            # identify what the value of the first one is
            first_appearance = pair[0]

            # identify what one needs to be replaced
            second_appearance = pair[1]

            # replace the second one
            surface_info['surface_num'][surface_info['surface_num']==second_appearance] = first_appearance

    # return processed dataframe
    return surface_info

def pair_logs(processed_surface_df, processed_log_df):
    """Combine the processed surface dataframe from Pupil with the processed
        log dataframe from PsychoPy to figure out which stimulus was shown
        at what time."""

    # only retain the stimulus logs
    stim_logs_only = (processed_log_df[processed_log_df['picture']!='reset_image']
                      .reset_index(drop=True))

    # associate the stimulus and surface numbers
    paired_logs = pd.DataFrame({'surface_num': processed_surface_df['surface_num'].unique(),
                                'stimulus_pic': stim_logs_only['picture'].unique()})

    # merge with the surface dataframe
    processed_surface_df = processed_surface_df.merge(paired_logs, on='surface_num')

    # return the merged dataframe
    return processed_surface_df

def associate_gaze_stimulus(gaze_surface_path, paired_log_df):
    """Add the stimulus ID and event (enter/exit) to each line of the gaze
        activity dataframe."""

    # read in the file with gaze surface information
    gaze_surface_df = pd.read_csv(gaze_surface_path)

    # take only a few columns from the paired_log_df
    limited_paired_logs = paired_log_df[['world_index',
                                         'stimulus_pic',
                                         'surface_and_event']]

    # merge the gaze logs and stimulus logs
    gaze_surface_df = (gaze_surface_df

                       # retain all gaze rows
                       .merge(limited_paired_logs,
                             on='world_index',
                             how='outer')

                       # fill all NAs with the previous value
                       .fillna(method='ffill'))

    # return the newly merged df
    return gaze_surface_df

def extract_survey(full_log_df):

    """Extract the participant's survey responses and reaction times (RT) for responding
        from the PsychoPy logfile."""

    # truncate time to 1 decimal place (without rounding)
    full_log_df['start_time'] = (full_log_df['start_time']
                                 .apply(lambda x: float( '%.1f'%(float(x)) )))

    # extract reaction time rows from full logfile
    rt_df = (full_log_df[(full_log_df['event'].str.contains('rating RT'))]
                         .reset_index(drop=True)
                         .drop(columns=['type','end_time','duration'])
                         .rename(columns={'start_time':'time',
                                          'event': 'rt'}))

    # extract the reaction time and convert to float
    rt_df['rt'] = (rt_df['rt'].str.extract('(\d+\.\d+)')
                              .astype(float))

    # extract question rows from full logfile
    question_df = (full_log_df[(full_log_df['event'].str.contains('Question'))]
                               .reset_index(drop=True)
                               .drop(columns=['type', 'end_time', 'duration'])
                               .rename(columns={'start_time':'time'}))

    # extract questions and responses from comma-separated line in 'event' variable
    concat_responses = question_df['event'].str.split(',', expand=True)
    question_df['question_number'] = concat_responses[0].str.extract('(\d+)').astype(int)
    question_df['rating'] = concat_responses[1].str.extract('(\d+)').astype(int)
    question_df = question_df.drop(columns='event')

    # mark whether the question came from before or after the Cyberball game
    question_df['survey'] = ((question_df

                              # tag pre- or post-cyberball survey
                              .groupby('question_number').cumcount()+1)
                              .astype(str)

                              # convert to string from numbers
                              .str.replace('1','pre')
                              .str.replace('2','post'))

    # join the question and reaction time dataframes
    joined_frame = question_df.join(rt_df,
                                    lsuffix='_q', rsuffix='_rt')

    # return the joined frame
    return joined_frame