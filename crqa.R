#### Scipt for running ANOVAs on SA data ####

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

# load librariies
library(stats)
library(readr)

### Prep for analyses ###

# read in radius files and bind together
files <- list.files(path = "./data/crqa_results/radius_calculations", pattern = "*.csv", full.names = T)
tbl <- sapply(files, read_csv, simplify=FALSE) %>% 
  bind_rows()

# create empty dataframe for saving filtered data
#filtered = data.frame()

# filtering for radii with closest rr to .05
filtered2 = tbl %>% ungroup() %>%
  dplyr::group_by(chosen.participant) %>%
  dplyr::filter(from.target == min(from.target))
  
# write the whole thing to a dataframe
write.table(filtered,
            './data/crqa_results/best_radius_calculations.csv',
            sep=',',
            col.names = TRUE,
            row.names = FALSE)

### Getting condition back ###

# Read in old downsampled data to get condition back
gaze_data = read.table('./data/downsampled/all_participants-downsampled.csv',
                       sep=',',header=TRUE)

# get unique participant and condition combos
gaze_data_simplified = gaze_data %>% ungroup() %>%
  group_by(participant, condition) %>% slice(1)

# merge condition back into filtered data
filtered = cbind(gaze_data_simplified, filtered)

#### ANOVAs ####

### % Determinism (det) and condition ###

# run the anova
det_anova <- aov(condition ~ det, data=filtered)

# summarize results
det_anova_results <- summary(det_anova)

# save results to file
capture.output(det_anova_results, file = './data/crqa_results/det_anova_results.txt')

### AMean Line (meanL) and condition ###

# run the anova
meanL_anova <- aov(condition ~ meanL, data=filtered)

# summarize results
meanL_anova_results <- summary(meanL_anova)

# save results to file
capture.output(meanL_anova_results, file = './data/crqa_results/meanL_anova_results.txt')
