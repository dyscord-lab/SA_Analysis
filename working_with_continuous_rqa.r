#### SA Analysis: Continuous RQA Parameter Searching ####
# [MC]: Created new subdirectory 'crqa_results' under 'data' for results!

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

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

# set maximum percentage of false nearest neighbors
fnnpercent = 10

next_ami = unique(gaze_data$ami.loc)[1]

# calculate false nearest neighbors
fnn = tseriesChaos::false.nearest(series = gaze_data$gaze_diff,
                                  m = fnnpercent,
                                  d = next_ami,
                                  t = 1,
                                  rt = 10,
                                  eps = sd(gaze_data$gaze_diff) / 10)
fnn = fnn[1,][complete.cases(fnn[1,])]
threshold = as.numeric(fnn[1]/fnnpercent)

# identify the largest dimension after a large drop
embed = max(as.numeric(which(diff(fnn) < -threshold))) + 1

# bind everything to data frame
gaze_data = gaze_data %>%
  mutate(embed = embed) 

# save false nearest neighbor calculations to file
write.table(gaze_data %>%
              select(participant, embed) %>%
              distinct(),
            './data/crqa_results/embed.csv', sep=',',row.names=FALSE,col.names=TRUE)

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

# cycle through all participants
for (next.particiant in gaze_crqa){

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
      print(paste("Participant ", unique(gaze_crqa$participant),
                  ": radius ",chosen.radius,sep=""))
      
      # identify parameters
      chosen.delay = unique(gaze_crqa$ami.loc)
      chosen.embed = unique(gaze_crqa$embed)
      
      # run CRQA and grab recurrence rate (RR)
      rec_analysis = crqa(gaze_crqa$rescale.gaze_diff, 
                          gaze_crqa$rescale.gaze_diff,
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
      write.table(cbind.data.frame(#participant,
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
                                          cbind.data.frame(participant,
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
