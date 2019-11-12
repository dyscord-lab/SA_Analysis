#### Data preparation for SA Study ####

# set working directory to repo
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

# set working directory 
setwd("./data/raw/analysis/")

install.packages('signal')

# load packages
library(dplyr)
library(signal)

#### Filtering out poorly tracked participants and creating difference value for gaze location ####

# create empty dataframe for saving filtered data
filtered = data.frame()

fileNames = list.files(path = "./")

fileList = list()
for(i in 1:length(fileNames)) {
  
<<<<<<< HEAD
  # read in participant file
  tempData = read.csv(fileNames[1])
  
  # creating diff variable for well-tracked participants only # moving to (< .2, > .7) for testing purposes (was <.05 & > .8)
  if (length(which(tempData$confidence == 0))/length(tempData$confidence) < .2 & length(which(tempData$confidence >= .8))/length(tempData$confidence) > .7) {
    
    # create diff variable
    tempData = tempData %>%
      mutate(gaze_diff = ((lag(norm_pos_x)-norm_pos_x)^2 + (lag(norm_pos_y)-norm_pos_y)^2)^(1/2)) 
    
    #### Downsampling ####
    
    # specify Butterworth filters
    anti_aliasing_butter = butter(4,.4)
    # post_downsample_butter = butter(2,.02)
    
    # downsample and take mean of each axis at new time scale
    gaze_data_downsampled = tempData[c(2:length(tempData$gaze_diff)),] %>%
      
      # retain only the variables we need
      select(gaze_timestamp, participant, gaze_diff, confidence, adjusted_timestamp, world_index, condition) %>%
      
      # convert time and participant to numeric
      mutate(t = as.numeric(gaze_timestamp)) %>%
      mutate(participant = as.numeric(participant)) %>%
      
      # apply anti-aliasing filter
      mutate(gaze_diff = signal::filtfilt(anti_aliasing_butter, gaze_diff)) %>% 
      
      # create new time variable to downsample
      mutate(t = floor(t * downsampled_sampling_rate) / downsampled_sampling_rate) %>% ungroup %>%
      
      # take means f
      summarize_each(funs(mean(.)))
      
      # filter again?
      #mutate(gaze_diff = signal::filtfilt(post_downsample_butter, gaze_diff)) # filter
    
    # plot to see if the data looks funny
    # ggplot(gaze_data_downsampled, aes(x = gaze_diff)) + geom_histogram()
    
    # filter again if the gaze data looks funny
    # mutate(euclid_accel = signal::filtfilt(post_downsample_butter, euclid_accel))
    
    # NOT WORKING:
    # save processed data to main dataframe
    filtered = rbind.data.frame(filtered, 
                                       gaze_data_downsampled)
   
  }
=======
  # filtering for awake participants (0% conf for < 1/20th of the data)
  dplyr::filter(sum(data$confidence == 0)/length(data$confidence) < .05) %>%
  
  # filtering for sufficient conf. participants (80+% conf for > 1/20th of the data)  
  dplyr::filter(sum(data$confidence >= .8)/length(data$confidence) > .8) %>% 
>>>>>>> 6c3382a84a3476c5d7383b304907973e4960e750
  
}


