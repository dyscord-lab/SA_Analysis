#### Script for grabbing other RQA metrics from phase 1 SA Study participants ####

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')
library(crqa)

## Setting up file to contain gaze data and optimal parameters ##

# read in filtered RQA parameter search results
filtered = read.table('./data/crqa_results/best_radius_calculations.csv',
                      sep=',',
                      header = TRUE)

# trim down to what we really need
filtered <- filtered[,c(1:4)]

# read in (downsampled) gaze csv of all participants
gaze_data = read.table('./data/downsampled/all_participants-downsampled.csv',
                       sep=',',header=TRUE)

# join the data frames
gaze_data = dplyr::full_join(gaze_data, filtered,
                             by = c('participant' = 'chosen.participant'))

# rescale diff by mean distance
gaze_crqa = gaze_data %>%
  dplyr::select(participant, gaze_diff) %>%
  group_by(participant) %>%
  mutate(rescale.gaze_diff = gaze_diff/mean(gaze_diff))
  
# create an empty dataframe to hold the parameter information
rqa_metrics = data.frame(participant = numeric(),
                         choosen.delay = numeric(),
                         chosen.embed = numeric(),
                         chosen.radius = numeric(),
                         rr = numeric(),
                         NRLINE = numeric(),
                         maxL = numeric(),
                         ENTR = numeric(),
                         rENTR = numeric(),
                         LAM = numeric(),
                         TT = numeric())

# split data into each particpant
participant.dfs = split(gaze_crqa,
                        list(gaze_crqa$participant))

# cycle through all participants
for (next.particiant in participant.dfs){
  
  # identify parameters
  chosen.delay = unique(next.particiant$chosen.delay)
  chosen.embed = unique(next.particiant$chosen.embed)
  chosen.radius = unique(next.particiant$chosen.radius)
  
  # run CRQA and grab recurrence rate (RR)
  rec_analysis = crqa(next.particiant$rescale.gaze_diff, 
                      next.particiant$rescale.gaze_diff,
                      delay = chosen.delay, 
                      embed = chosen.embed, 
                      r = chosen.radius,
                      normalize = 0, 
                      rescale = 0, 
                      mindiagline = 2,
                      minvertline = 2, 
                      tw = 1, 
                      whiteline = FALSE,
                      recpt = FALSE)
  
  # save all metrics to variables
  rr = rec_analysis$RR
  det = rec_analysis$DET
  meanL = rec_analysis$L
  NRLINE = rec_analysis$NRLINE
  maxL = rec_analysis$maxL
  ENTR = rec_analysis$ENTR
  rENTR = rec_analysis$rENTR
  LAM = rec_analysis$LAM
  TT = rec_analysis$TT
  
  # save results
  write.table(cbind.data.frame(unique(next.participant$participant),
                               chosen.delay,
                               chosen.embed,
                               chosen.radius,
                               rr,
                               det,
                               meanL,
                               NRLINE,
                               maxL,
                               ENTR,
                               rENTR,
                               LAM,
                               TT),
              paste('./data/crqa_results/rqa_metrics-', unique(next.participont$particiant),'.csv', sep=''), 
              sep=',',row.names=FALSE,col.names=TRUE)
  
  # append to dataframe
  rqa_metrics = rbind.data.frame(rqa_metrics,
                                 cbind.data.frame(unique(next.participant$participant),
                                                  chosen.delay,
                                                  chosen.embed,
                                                  chosen.radius,
                                                  rr,
                                                  det,
                                                  meanL,
                                                  NRLINE,
                                                  maxL,
                                                  ENTR,
                                                  rENTR,
                                                  LAM,
                                                  TT))
}

# save the radius explorations to file
write.table(rqa_metrics,'./data/crqa_results/all_rqa_metrics-SA.csv', sep=',',row.names=FALSE,col.names=TRUE)
