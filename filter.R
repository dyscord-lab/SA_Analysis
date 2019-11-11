### Filtering out low confidence eye-tracking and  ###
### creating difference variable for gaze location ###

# set working directory 
setwd("./SA_Analysis/")

# load packages
library(dplyr)

# read in full csv of all participant gaze data
data = read.csv('./data/', 
                sep=",") %>%
  
  # grouping by participant
  group_by(participantID) %>%
  
  # filtering for awake participants (0% conf for < 1/20th of the data)
  dplyr::filter(sum(data$confidence == 0)/length(data$confidence) < .05) %>%
  
  # filtering for sufficient conf. participants (80+% conf for > 1/20th of the data)  
  dplyr::filter(sum(data$confidence >= .8)/length(data$confidence) > .8) %>% 
  
  # creating difference value in Cartesian coordinates for remaining participants
  mutate(diff = ((lag(x_norm)-x_norm)^2 + (lag(y_norm)-y_norm)^2)^(1/2)) 
