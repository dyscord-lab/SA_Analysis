#### Script for generating an example CRP for Psychonomics poster ####

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

# read in gaze csv of all participants
gaze_data = read.table('./data/downsampled/all_participants-downsampled.csv',
                       sep=',',header=TRUE)

# grab one participants data
one.participant <- gaze_data[which(gaze_data$participant == 'sa1_2019-10-22_001-0'),]
delay = 6
embed = 3
radius = .05

# run CRQA and grab recurrence rate (RR)
rec_analysis = crqa(one.participant$gaze_diff, 
                    one.participant$gaze_diff,
                    delay = delay, 
                    embed = embed, 
                    r = radius,
                    normalize = 0, 
                    rescale = 1, 
                    mindiagline = 2,
                    minvertline = 2, 
                    tw = 1, 
                    whiteline = FALSE,
                    recpt = FALSE)

# convert to data frame
cross_rqa_df = data.frame(points = rec_analysis$RP@i,
                          loc = seq_along(rec_analysis$RP@i))

# generate the CRP
ggplot(cross_rqa_df,aes(x=points,
                        y=loc)) +
  geom_point(color="black",size=.7) +
  theme_classic() +
  theme(legend.position="none", axis.text.x = element_blank(), axis.text.y = element_blank()) +
  ylab("") + xlab("") +
  ggtitle("Cross-Recurrence Plot")

# save plot
ggsave("./data/crqa_results/CRP_example.png")



