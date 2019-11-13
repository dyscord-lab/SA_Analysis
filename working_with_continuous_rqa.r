#### SA Analysis: Continuous RQA Parameter Searching ####
# [MC]: Created new subdirectory 'crqa_results' under 'data' for results!

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')
library(crqa)

# read in gaze csv of all participants
gaze_data = read.table('./data/downsampled/all_participants-downsampled.csv',
                       sep=',',header=TRUE)

#### Determine DELAY with average mutual information (AMI) ####

# set maximum AMI
ami.lag.max = 200

# get AMI lag
gaze_data = gaze_data %>%
  
  # group data of each participant
  group_by(participant) %>%
  
  # find first local minimum
  mutate(ami.loc = first_local_minimum(tseriesChaos::mutual(gaze_diff, lag.max = ami.lag.max, plot = FALSE)))

ami_df = gaze_data %>%
  select(participant, ami.loc) %>%
  distinct()
# 
# test_df = gaze_data %>%
#   dplyr::filter(participant == 'sa1_2019-10-31_001-0')
# 
# test_ami = tseriesChaos::mutual(test_df$gaze_diff, lag.max = ami.lag.max, plot = TRUE)

# write AMI information to file
write.table(gaze_data %>%
              select(participant, ami.loc) %>%
              distinct(),
            './data/crqa_results/ami.csv',
            sep=',',
            row.names=FALSE, col.names=TRUE)

#### Determing embedding dimension with FNN ####

# create empty data frame for saving embed results
embed_results = data.frame()

# set maximum percentage of false nearest neighbors
fnnpercent = 10

# split up data into each participant
participant.dfs = split(gaze_data,
                  list(gaze_data$participant))

# loop through each participant file to calculate fNN
for (next.participant in participant.dfs) {
  
  # call in the needed data
  next_participant = data.frame(next.participant)
  
  # tell us whats up
  print(paste0("Beginning fNN calculations for participant ", unique(next_participant$participant)))
  
  # grab unique ami for the participant
  next_ami = unique(next_participant$ami.loc)[1]
  
  # calculate false nearest neighbors
  fnn = tseriesChaos::false.nearest(series = next_participant$gaze_diff,
                                    m = fnnpercent,
                                    d = next_ami,
                                    t = 1,
                                    rt = 10,
                                    eps = sd(next_participant$gaze_diff) / 10)
  fnn = fnn[1,][complete.cases(fnn[1,])]
  threshold = as.numeric(fnn[1]/fnnpercent)
  
  # identify the largest dimension after a large drop
  embed = max(as.numeric(which(diff(fnn) < -threshold))) + 1
  
  next_participant = next_participant %>%
    mutate(embed = embed) 
  
  embed_results = rbind.data.frame(embed_results,
                              next_participant)
}

# save false nearest neighbor calculations to file
write.table(embed_results %>%
              select(participant, embed) %>%
              distinct(),
            './data/crqa_results/embed.csv', sep=',',row.names=FALSE,col.names=TRUE)

gaze_data = full_join(gaze_data, embed_results)

#### Determine optimal radius ####

# rescale by mean distance
gaze_crqa = gaze_data %>%
  dplyr::select(participant, gaze_diff, ami.loc, embed) %>%
  group_by(participant) %>%
  mutate(rescale.gaze_diff = gaze_diff/mean(gaze_diff))

# create an empty dataframe to hold the parameter information
radius_selection = data.frame(participant = numeric(),
                              choosen.delay = numeric(),
                              chosen.embed = numeric(),
                              chosen.radius = numeric(),
                              rr = numeric())

# identify radius for calculations
radius.list = seq(.05,.20,by=.05)

# split up data into each participant
participant.dfs = split(gaze_crqa,
                        list(gaze_crqa$participant))

# cycle through all participants
for (next.particiant in participant.dfs){
  
  # reset `target` variables for new radius (above what RR can be)
  from.target = 101
  last.from.target = 102
  
  # cycle through radii
  for (chosen.radius in radius.list){
    
    # if we're still improving, keep going
    if (from.target < last.from.target){
      
      # keep the previous iteration's performance
      last.from.target = from.target
      
      # print update
      print(paste("Participant ", unique(next.particiant$participant),
                  ": radius ", chosen.radius,sep=""))
      
      # identify parameters
      chosen.delay = unique(next.particiant$ami.loc)
      chosen.embed = unique(next.particiant$embed)
      
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
                          tw = 0, 
                          whiteline = FALSE,
                          recpt = FALSE)
      rr = rec_analysis$RR
      det = rec_analysis$DET
      meanL = rec_analysis$L
      
      # clear it so we don't take up too much memory (optional)
      rm(rec_analysis)
      
      # identify how far off the RR is from our target (5%)
      from.target = abs(rr - 5)
      
      # save individual radius calculations
      write.table(cbind.data.frame(unique(next.participant$participant),
                                   chosen.delay,
                                   chosen.embed,
                                   chosen.radius,
                                   rr,
                                   det,
                                   meanL,
                                   from.target),
                  paste('./data/crqa_results/radius_calculations-mean_scaled-r',chosen.radius,'-', particiant,'.csv', sep=''), 
                  sep=',',row.names=FALSE,col.names=TRUE)
      
      # append to dataframe
      radius_selection = rbind.data.frame(radius_selection,
                                          cbind.data.frame(unique(next.participant$participant),
                                                           chosen.delay,
                                                           chosen.embed,
                                                           chosen.radius,
                                                           rr,
                                                           det,
                                                           meanL,
                                                           from.target))
    } else {
      
      # if we're no longer improving, break
      break
      
    }}}

# save the radius explorations to file
write.table(radius_selection,'./data/crqa_results/radius_calculations-mean_scaled-SA.csv', sep=',',row.names=FALSE,col.names=TRUE)

# let us know when it's finished
beepr::beep("fanfare")

#### Export chosen radii for all participants ####

# load in files
radius_selection = read.table('./data/crqa_results/radius_calculations-mean_scaled-SA.csv',
                              sep=',',header=TRUE)

# identify the target radii
radius_stats = radius_selection %>% ungroup() %>%
  group_by(participant) %>%
  dplyr::filter(from.target==min(from.target)) %>%
  dplyr::arrange(participant) %>%
  dplyr::arrange(desc(from.target)) %>%
  slice(1) %>%
  distinct()

# join the dataframes
gaze_crqa = full_join(radius_stats,
                                 gaze_crqa,
                                 by = c("participant",
                                        "chosen.embed" = "embed.selected",
                                        "chosen.delay" = "ami.selected"))

# save to files
write.table(gaze_crqa,'./data/crqa_results/crqa_data_and_parameters-SA.csv', 
            sep=',',row.names=FALSE,col.names=TRUE)
write.table(radius_stats, './data/crqa_results/crqa_parameters-SA.csv',
            sep=',',row.names=FALSE,col.names=TRUE)
