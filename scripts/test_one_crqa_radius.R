#! /usr/bin/env Rscript

##### Parallelizing RQA radius search #####

# With thanks to https://github.com/FredHutch/slurm-examples/blob/master/centipede/example.R
# and https://sph.umich.edu/biostat/computing/cluster/examples/r.html.

# grab the array id value from the environment variable passed from sbatch
slurm_arrayid = Sys.getenv('SLURM_ARRAY_TASK_ID')

# coerce the value to an integer
n = as.numeric(slurm_arrayid)

# load libraries
library(crqa)
library(dplyr)

# read the data
gaze_crqa = read.table('./data/crqa_results/crqa_data-rescaled_with_parameters.csv',
                       sep=',', header = TRUE)

# read in embedding dimensions
embed_dimensions=read.table('./data/crqa_results/embed.csv',
                            sep=',', header = TRUE)

# not sure why, but trying to write the table WITH the embedding dimensions leads to NAs
# (will need to troubleshoot later)
gaze_crqa = gaze_crqa %>% 
  select(-embed) %>%
  dplyr::full_join(., embed_dimensions)

# identify radius for calculations
radius.list = seq(.05,.18,by=.01)

# create a grid
radius_grid_search = expand.grid(radius.list,
                                 unique(gaze_crqa$participant))

# identify what set we're doing right now
chosen.radius = as.numeric(radius_grid_search[n,1])
print('Chosen delay: ', str(chosen.radius))
chosen.participant = radius_grid_search[n,2]
print('Chosen participant: ', str(chosen.participant))

# subset the data
next.participant = gaze_crqa %>%
  dplyr::filter(participant == chosen.participant)
rm(gaze_crqa)

# identify parameters
chosen.delay = unique(next.participant$ami.loc)
print('Chosen delay: ', str(chosen.delay))
chosen.embed = unique(next.participant$embed)
print('Chosen embedding dimension: ', str(chosen.embed))

# run CRQA and grab recurrence rate (RR)
rec_analysis = crqa(next.participant$rescale.gaze_diff,
                    next.participant$rescale.gaze_diff,
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
rr = rec_analysis$RR
det = rec_analysis$DET
meanL = rec_analysis$L

# clear it so we don't take up too much memory (optional)
rm(rec_analysis)

# identify how far off the RR is from our target (5%)
from.target = abs(rr - 5)
print(from.target)

# save individual radius calculations
write.table(cbind.data.frame(chosen.participant,
                             chosen.delay,
                             chosen.embed,
                             chosen.radius,
                             rr,
                             det,
                             meanL,
                             from.target),
            paste('./data/crqa_results/radius_calculations/radius_calculations-mean_scaled-r',chosen.radius,'-', chosen.participant,'.csv', sep=''),
            sep=',',row.names=FALSE,col.names=TRUE)
