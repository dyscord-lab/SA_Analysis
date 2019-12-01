# import libraries that we need
import os
import csv
import pandas as pd
from datetime import datetime


# Handles the general sorting
class Sorting:
    def __init__(self, savelogs):
        self.imgsorder = []
        self.surfaces = []
        self.offset = 0
        self.pupil_offset = 0  # meant to replace offset, if method accepted
        self.log_offset = 0
        self.savelogs = savelogs

    # Calculates the offset time for the Pupil timestamps and the Log's times, both into proper epoch time
    # log_offset = (time the file was last modified) - ("END" time in the log)
    # pupil_offset = System Time - Synced/Pupil time
    def calc_offsets(self, infofile, logfile, log_timestamps):
        """
        The modified time always stays consistent, as long as no one touches the file (which they shouldn't)
        Creation time is inaccurate if they're copied to a new location (vs moved) + platform dependent
        """
        log_file_closed = os.path.getmtime(logfile)  # epoch time, seconds
        log_exp_end = log_timestamps.apply(float).max()
        self.log_offset = log_file_closed - log_exp_end

        # defined by Pupil Labs in issue#1500 (https://git.io/Je2w1)
        with open(infofile) as f:
            system, synced = None, None
            reader = csv.reader(f)

            for row in reader:
                if '(System)' in row[0]:
                    system = float(row[1])
                elif '(Synced)' in row[0]:
                    synced = float(row[1])
            if system and synced:
                self.pupil_offset = system - synced

    def logsort(self, log_file_path, infofile_path):
        """ Parse the PsychoPy logfile."""

        # read in the file as a dataframe
        fullinfo = (pd.read_csv(log_file_path, sep='\t', header=None)

                    # rename columns
                    .rename(columns={0: "adjusted_timestamp",
                                     1: "type",
                                     2: "event"})

                    # drop any participant responses
                    .dropna())
        fullinfo['adjusted_timestamp'] = fullinfo['adjusted_timestamp'].apply(float)
        self.calc_offsets(log_file_path, infofile_path, fullinfo['adjusted_timestamp'])

        # identify only the events where images occurred
        only_pics = (fullinfo[fullinfo['event'].str.contains("PICTURE")]
                     .reset_index(drop=True)
                     .drop(columns='type')
                     .rename(columns={'event': 'picture'}))

        # leave only picture numbers for picture identification
        only_pics['picture'] = (only_pics['picture'].str.replace('PICTURE: ', '')
                                .str.replace('.png', ''))

        # save image order
        self.imgsorder = [int(x) for x in only_pics.picture.unique()
                          if x != "reset_image"]

        # return the picture dataframe
        return fullinfo, only_pics

    # Iterates over a timestamps column + converts to unix epoch time
    def convert_times(self, timestamp_col, offset_type):
        """
        log_timestamp + log_offset <=> pupil_timestamp + pupil_offset

        an example call would be
        gaze_surface_df['adjusted_timestamp'] = self.convert_times(gaze_surface_df['adjusted_timestamp'],
                                                                   self.pupil_offset)
        """
        adjusted = []

        for timestamp in timestamp_col:
            new_time = timestamp + offset_type
            adjusted.append(new_time)

        # to be added as new column in dataframe
        return adjusted

    # Collects the gazes timestamp, instead of the world_timestamps
    # Levels out the gaze times to that of the log file
    def adjust_timestamps(self, gaze_surface_df, logfile_image_df,
                          gaze_timestamp_colname="gaze_timestamp",
                          logfile_timestamp_colname="adjusted_timestamp",
                          round_places=4):

        """Attempt to adjust the gaze timestamps to match with the logfile
            timestamps.

            By default, round resulting timestamps to 4 places.

            By default, assume `gaze_surface_df` and `logfile_df` to have time
            variables `gaze_timestamp` and `adjusted_timestamp`, respectively."""

        # identify first time in the gazesurface file
        gaze_offset = gaze_surface_df[gaze_timestamp_colname].apply(float).min()

        # identify first time that PsychoPy logged an image
        log_offset = logfile_image_df[logfile_timestamp_colname].apply(float).min()

        # identify total offset
        total_offset = (-gaze_offset + log_offset)

        # create a timestamp adjusted to the logfile time
        gaze_surface_df['adjusted_timestamp'] = gaze_surface_df['gaze_timestamp'] + total_offset
        gaze_surface_df['adjusted_timestamp'] = gaze_surface_df['adjusted_timestamp'].round(round_places)

        # return df with new adjusted variable
        self.offset = total_offset
        return gaze_surface_df


def process_surfaces(surface_events_path, full_gaze_path):
    """Process surface events file from Pupil Player."""

    # read surface events file to dataframe
    surface_info = (pd.read_csv(surface_events_path)
                    .drop(columns='surface_name'))

    # sequence surface names and events
    surface_info['surface_num'] = surface_info.groupby('event_type').cumcount() + 1

    # concatenate variables
    surface_info['surface_and_event'] = (surface_info['event_type']
                                         + '_'
                                         + surface_info['surface_num'].map(str))

    # read the full gazefile path
    full_gaze_df = (pd.read_csv(full_gaze_path)
                    .drop(columns=['base_data',
                                   'eye_center1_3d_x', 'eye_center1_3d_y', 'eye_center1_3d_z',
                                   'eye_center0_3d_x', 'eye_center0_3d_y', 'eye_center0_3d_z',
                                   'gaze_point_3d_x', 'gaze_point_3d_y', 'gaze_point_3d_z',
                                   'gaze_normal0_x', 'gaze_normal0_y', 'gaze_normal0_z',
                                   'gaze_normal1_x', 'gaze_normal1_y', 'gaze_normal1_z']))

    # merge the two
    merged_surfaces = (full_gaze_df.merge(surface_info, how='outer', on='world_index')
                       .fillna(method='ffill')
                       .reset_index(drop=True))
    merged_surfaces = (merged_surfaces[merged_surfaces['world_index'] > surface_info['world_index'].min()]
                       .reset_index(drop=True))

    # return processed dataframe
    return merged_surfaces


def merge_all_dataframes(processed_surfaces_df, gaze_surface_df, processed_image_df):
    """Combine everything we've been working on into a single dataframe"""

    # merge surface-specific and surface-agnostic dataframes
    all_gaze_df = (processed_surfaces_df.merge(gaze_surface_df,
                                               how="outer", on=['gaze_timestamp', 'adjusted_timestamp',
                                                                'world_index', 'confidence'])
                   .sort_values(by=['gaze_timestamp'])
                   .reset_index(drop=True))

    # merge resulting dataframe with image logs
    gaze_and_img_df = (all_gaze_df.merge(processed_image_df,
                                         how="outer",
                                         on='adjusted_timestamp')
                       .sort_values(by=['adjusted_timestamp'])
                       .reset_index(drop=True))

    # forward-fill picture information
    gaze_and_img_df['picture'] = gaze_and_img_df['picture'].fillna(method='ffill')

    # return the resulting dataframe
    return gaze_and_img_df


def extract_survey(full_log_df, survey_key_df):
    """Extract the participant's survey responses and reaction times (RT) for responding
        from the PsychoPy logfile."""

    # truncate time to 1 decimal place (without rounding)
    full_log_df['adjusted_timestamp'] = (full_log_df['adjusted_timestamp']
                                         .apply(lambda x: float('%.1f' % (float(x)))))

    # extract reaction time rows from full logfile
    rt_df = (full_log_df[(full_log_df['event'].str.contains('rating RT'))]
             .reset_index(drop=True)
             .drop(columns=['type'])
             .rename(columns={'adjusted_timestamp': 'time',
                              'event': 'rt'}))

    # extract the reaction time and convert to float
    rt_df['rt'] = (rt_df['rt'].str.extract('(\d+\.\d+)')
                   .astype(float))

    # extract question rows from full logfile
    question_df = (full_log_df[(full_log_df['event'].str.contains('Question'))]
                   .reset_index(drop=True)
                   .rename(columns={'adjusted_timestamp': 'time'}))

    # extract questions and responses from comma-separated line in 'event' variable
    concat_responses = question_df['event'].str.split(',', expand=True)
    question_df['question_number'] = concat_responses[0].str.extract('(\d+)').astype(int)
    question_df['rating'] = concat_responses[1].str.extract('(\d+)').astype(int)
    question_df = question_df.drop(columns='event')

    # mark whether the question came from before or after the Cyberball game
    question_df['survey'] = ((question_df

                              # tag pre- or post-cyberball survey
                              .groupby('question_number').cumcount() + 1)
                             .astype(str)

                             # convert to string from numbers
                             .str.replace('1', 'pre')
                             .str.replace('2', 'post'))

    # join the question and reaction time dataframes
    joined_frame = question_df.join(rt_df,
                                    lsuffix='_q', rsuffix='_rt')

    # join with the questions
    joined_frame = joined_frame.merge(survey_key_df,
                                      how='outer',
                                      on='question_number')

    # return the joined frame
    return joined_frame
