#### Data preparation for SA Study ####

## NOTE: The `analysis` subdirectory should be directly under the
##       `data` directory.

## NOTE: In `data`, you must make a subdirectory called `downsampled`.
##       In the new `downsampled` subdirectory, you must make a new 
##       subdirectory called `individual`.

# set working directory to repo
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

# load packages
library(dplyr)
library(signal)

#### Filtering out poorly tracked participants and creating difference value for gaze location ####

# grab all files in the data analysis folder
##    [AP] I didn't see a call to look for the files in the previous version 
##         (which may have been contributing to the issues).
participant_files = list.files('./data/analysis',full.names = TRUE)

# create empty dataframe for saving filtered data
filtered = data.frame()

# cycle through all files
for(i in 1:length(participant_files)) {
  
  ## [AP] When you can't get a loop to work, one suggestion is to have the
  ##      loop or store everything that you're calculating so that you can
  ##      figure out where the breakdown occurs.
  print(participant_files[i])
  
  # read in participant file
  ##    [AP] One reason why this may not have worked is because this was always 
  ##         reading in the first file, rather than the `i`th file.
  #tempData = read.csv(participant_files[1])
  tempData = read.csv(participant_files[i])
  
  # identify when the last reset_image appeared
  final_reset_t = tempData %>% ungroup() %>%
    
    # get the timestamps for when each image appears
    select(picture, adjusted_timestamp, surface_num) %>%
    distinct() %>%
    group_by(picture, surface_num) %>%
    slice(1) %>%
    ungroup() %>%
    
    # identify the last time the reset_image appears
    dplyr::filter(picture=='reset_image') %>%
    slice(n()) %>%
    .$adjusted_timestamp
  
  # remove anything that happened after the last reset image appeared
  tempData = tempData %>% ungroup() %>%
    dplyr::filter(adjusted_timestamp < final_reset_t)
  
  # creating diff variable for well-tracked participants only
  if (length(which(tempData$confidence == 0))/length(tempData$confidence) < .1 
      && length(which(tempData$confidence >= .8))/length(tempData$confidence) > .7) {
    
    # create diff variable
    tempData = tempData %>%
      mutate(gaze_diff = ((lag(norm_pos_x)-norm_pos_x)^2 + (lag(norm_pos_y)-norm_pos_y)^2)^(1/2)) %>%
      
      # if confidence is 0, don't calculate a diff
      mutate(gaze_diff = ifelse(confidence == 0,
                                NA,
                                gaze_diff)) %>%
      
      # if the previous sample had a confidence of 0, don't calculate a diff
      mutate(previous_confidence = dplyr::lag(confidence, n=1)) %>%
      mutate(gaze_diff = ifelse(previous_confidence == 0,
                                NA,
                                gaze_diff)) %>%
      select(-previous_confidence) %>%
      
      # remove any samples that didn't have a diff
      na.omit()
    
    #### Downsampling ####
    
    # specify Butterworth filters
    anti_aliasing_butter = butter(4,.4)
    # post_downsample_butter = butter(2,.02)
    
    # downsample and take mean of each axis at new time scale
    gaze_data_downsampled = tempData %>%
      
      # retain only the variables we need
      select(gaze_timestamp, adjusted_timestamp, world_index,
             participant, condition, picture, gaze_diff, confidence,) %>%
      
      # convert time to numeric
      mutate(t = as.numeric(gaze_timestamp)) %>%
      
      # convert `reset_image` to numeric
      mutate(picture = ifelse(picture=='reset_image',
                              999,
                              picture)) %>%
      
      # apply anti-aliasing filter
      mutate(gaze_diff = signal::filtfilt(anti_aliasing_butter, gaze_diff)) %>% 
      
      # create new time variable to downsample
      mutate(t = floor(t * downsampled_sampling_rate) / downsampled_sampling_rate) %>% 
      
      # since we have images that can change within each second, just take the first slice
      group_by(t) %>%
      slice(1) %>%
      ungroup()
    
    
    # plot to see if the data looks funny
    # ggplot(gaze_data_downsampled, aes(x = gaze_diff)) + geom_histogram()
    
    # # filter again if the gaze data looks funny
    # gaze_data_downsampled = gaze_data_downsampled %>% 
    #   mutate(euclid_accel = signal::filtfilt(post_downsample_butter, euclid_accel))
    
    # write it to a file
    write.table(gaze_data_downsampled, 
                paste0('./data/downsampled/individual/',
                       unique(gaze_data_downsampled$participant)[1],
                       '-downsampled.csv'),
                sep=',',
                col.names = TRUE,
                row.names = FALSE)
    
    # save processed data to main dataframe
    filtered = rbind.data.frame(filtered, 
                                gaze_data_downsampled)
  }
}

# write the whole thing to a dataframe
write.table(filtered,
            './data/downsampled/all_participants-downsampled.csv',
            sep=',',
            col.names = TRUE,
            row.names = FALSE)

