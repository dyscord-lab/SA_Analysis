import os
import pandas as pd

def export_files(participant_info, top_root,
                 gaze_df, survey_df):
    
    """Export file and gaze data in original formats and in 
        analysis-ready format"""

    # set variables we need
    condition = participant_info[-1]
    
    # save the final gaze dataframe
    gaze_filename = participant_info + '-complete_gaze_df.csv'
    gaze_df['participant'] = participant_info
    gaze_df['condition'] = condition
    gaze_df.to_csv(top_root + '/processed/' + gaze_filename,
                   index=None)

    # save the final survey dataframe
    survey_filename = participant_info + '-survey_df.csv'
    survey_df['participant'] = participant_info
    survey_df['condition'] = condition
    survey_df.to_csv(top_root + '/processed/' + survey_filename, 
                     index=None)

    # prepare a version for analysis
    gaze_df = (gaze_df.drop(columns=['world_timestamp_x',
                                     'world_timestamp_y',
                                     'x_norm','y_norm',
                                     'x_scaled','y_scaled',
                                     'surface_and_event']))

    # say anything with a missing surface wasn't on the surface
    gaze_df['on_surf'] = gaze_df['on_surf'].fillna(False)

    # remove any remaining rows with NAs and include the participant info
    gaze_df = gaze_df.dropna(axis=0)
    gaze_df['participant'] = participant_info
    gaze_df['condition'] = condition
    
    # save the final dataframe
    gaze_filename = participant_info + '-analysis_df.csv'
    gaze_df.to_csv(top_root + '/analysis/' + gaze_filename,
                   index=None)